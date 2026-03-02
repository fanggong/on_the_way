import { useEffect, useMemo, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  Button,
  Card,
  Empty,
  Input,
  InputNumber,
  Select,
  Space,
  Switch,
  Table,
  Toast,
  Typography,
} from '@douyinfe/semi-ui';

import { useAuth } from '../contexts/AuthContext';
import {
  ConnectorOption,
  createBackfillJob,
  getSyncJobs,
  getSystemSources,
  updateConnectorEnabled,
  updateCoreSource,
  updateSyncPolicy,
} from '../services/api';

interface SyncDraft {
  auto_sync_enabled: boolean;
  auto_sync_interval_minutes: number;
}

export function SystemSourcesPage() {
  const { accessToken, hasPermission } = useAuth();
  const writable = hasPermission('system_source.write');

  const systemSourceQuery = useQuery({
    queryKey: ['system-sources', accessToken],
    queryFn: () => getSystemSources(accessToken ?? ''),
    enabled: Boolean(accessToken),
  });

  const healthJobsQuery = useQuery({
    queryKey: ['system-sync-jobs-health', accessToken],
    queryFn: () => getSyncJobs(accessToken ?? '', 'health'),
    enabled: Boolean(accessToken),
  });

  const [coreDraft, setCoreDraft] = useState<Record<string, string>>({});
  const [syncDraft, setSyncDraft] = useState<Record<string, SyncDraft>>({});
  const [backfillStartAt, setBackfillStartAt] = useState('');
  const [backfillEndAt, setBackfillEndAt] = useState('');

  useEffect(() => {
    if (!systemSourceQuery.data) {
      return;
    }

    const nextCoreDraft: Record<string, string> = {};
    const nextSyncDraft: Record<string, SyncDraft> = {};

    systemSourceQuery.data.items.forEach((item) => {
      nextCoreDraft[item.system_code] = item.core_source.connector_code ?? '';
      nextSyncDraft[item.system_code] = {
        auto_sync_enabled: item.core_source.auto_sync_enabled,
        auto_sync_interval_minutes: item.core_source.auto_sync_interval_minutes,
      };
    });

    setCoreDraft(nextCoreDraft);
    setSyncDraft(nextSyncDraft);
  }, [systemSourceQuery.data]);

  const sourceItems = systemSourceQuery.data?.items ?? [];

  const healthSource = useMemo(
    () => sourceItems.find((item) => item.system_code === 'health') ?? null,
    [sourceItems],
  );

  const handleEnableConnector = async (
    systemCode: string,
    connectorCode: string,
    enabled: boolean,
  ) => {
    if (!accessToken || !writable) {
      return;
    }

    try {
      await updateConnectorEnabled(accessToken, systemCode, connectorCode, enabled);
      Toast.success('连接器状态已更新');
      await systemSourceQuery.refetch();
    } catch (error) {
      Toast.error(error instanceof Error ? error.message : '更新失败');
    }
  };

  const handleSaveCoreSource = async (systemCode: string) => {
    if (!accessToken || !writable) {
      return;
    }

    const connectorCode = coreDraft[systemCode];
    if (!connectorCode) {
      Toast.error('请选择核心连接器');
      return;
    }

    try {
      await updateCoreSource(accessToken, systemCode, connectorCode);
      Toast.success('核心数据源已更新');
      await systemSourceQuery.refetch();
    } catch (error) {
      Toast.error(error instanceof Error ? error.message : '更新核心数据源失败');
    }
  };

  const handleSaveSyncPolicy = async (systemCode: string) => {
    if (!accessToken || !writable) {
      return;
    }

    const draft = syncDraft[systemCode];
    if (!draft) {
      return;
    }

    try {
      await updateSyncPolicy(accessToken, systemCode, draft);
      Toast.success('同步策略已更新');
      await systemSourceQuery.refetch();
    } catch (error) {
      Toast.error(error instanceof Error ? error.message : '更新同步策略失败');
    }
  };

  const handleCreateBackfill = async () => {
    if (!accessToken || !writable) {
      return;
    }

    if (!backfillStartAt || !backfillEndAt) {
      Toast.error('请填写回填开始与结束时间');
      return;
    }

    try {
      await createBackfillJob(accessToken, 'health', {
        backfill_start_at: backfillStartAt,
        backfill_end_at: backfillEndAt,
      });
      Toast.success('回填任务已提交');
      await Promise.all([systemSourceQuery.refetch(), healthJobsQuery.refetch()]);
    } catch (error) {
      Toast.error(error instanceof Error ? error.message : '提交任务失败');
    }
  };

  return (
    <Space vertical spacing="medium" style={{ width: '100%' }}>
      <Card title="系统数据源管理" shadows="hover">
        <Typography.Text type="tertiary">
          每个系统仅允许一个核心数据源。自动同步策略只对核心连接器生效；单次回填任务不会修改自动同步频率。
        </Typography.Text>
        {!writable ? (
          <Typography.Text type="warning" style={{ display: 'block', marginTop: 8 }}>
            当前账号无 `system_source.write` 权限，仅可查看，不能修改连接器与同步策略。
          </Typography.Text>
        ) : null}
      </Card>

      {sourceItems.length === 0 ? (
        <Card>
          <Empty title="暂无系统数据源配置" />
        </Card>
      ) : (
        sourceItems.map((item) => {
          const options = item.available_connectors;
          const enabledOptions = options.filter((option) => option.enabled);
          const sync =
            syncDraft[item.system_code] ??
            ({ auto_sync_enabled: false, auto_sync_interval_minutes: 60 } satisfies SyncDraft);

          return (
            <Card key={item.system_code} title={`${item.system_name} (${item.system_code})`} shadows="hover">
              <Space vertical align="start" style={{ width: '100%' }}>
                {options.length === 0 ? (
                  <Typography.Text type="tertiary">暂无可选连接器</Typography.Text>
                ) : (
                  options.map((option: ConnectorOption) => (
                    <div className="inline-row" key={`${item.system_code}-${option.connector_code}`}>
                      <Typography.Text>
                        {option.display_name} ({option.connector_code})
                      </Typography.Text>
                      <Switch
                        checked={option.enabled}
                        onChange={(checked) => {
                          void handleEnableConnector(item.system_code, option.connector_code, checked);
                        }}
                        disabled={!writable}
                      />
                    </div>
                  ))
                )}

                <div className="inline-row wrap">
                  <Typography.Text>核心数据源</Typography.Text>
                  <Select
                    style={{ width: 280 }}
                    value={coreDraft[item.system_code]}
                    onChange={(value) => {
                      setCoreDraft((prev) => ({
                        ...prev,
                        [item.system_code]: String(value ?? ''),
                      }));
                    }}
                    placeholder={enabledOptions.length ? '请选择核心连接器' : '暂无可选连接器'}
                    optionList={enabledOptions.map((option) => ({
                      label: option.display_name,
                      value: option.connector_code,
                    }))}
                    disabled={enabledOptions.length === 0 || !writable}
                  />
                  <Button
                    onClick={() => void handleSaveCoreSource(item.system_code)}
                    disabled={!enabledOptions.length || !writable}
                  >
                    保存核心数据源
                  </Button>
                </div>

                <div className="inline-row wrap">
                  <Typography.Text>自动同步</Typography.Text>
                  <Switch
                    checked={sync.auto_sync_enabled}
                    onChange={(checked) => {
                      setSyncDraft((prev) => ({
                        ...prev,
                        [item.system_code]: {
                          ...sync,
                          auto_sync_enabled: checked,
                        },
                      }));
                    }}
                    disabled={!item.core_source.connector_code || !writable}
                  />
                  <InputNumber
                    min={15}
                    max={1440}
                    value={sync.auto_sync_interval_minutes}
                    onChange={(value) => {
                      setSyncDraft((prev) => ({
                        ...prev,
                        [item.system_code]: {
                          ...sync,
                          auto_sync_interval_minutes:
                            typeof value === 'number' ? value : sync.auto_sync_interval_minutes,
                        },
                      }));
                    }}
                    style={{ width: 160 }}
                    disabled={!item.core_source.connector_code || !writable}
                  />
                  <Button
                    type="secondary"
                    onClick={() => void handleSaveSyncPolicy(item.system_code)}
                    disabled={!item.core_source.connector_code || !writable}
                  >
                    保存同步策略
                  </Button>
                </div>

                <Typography.Text type="tertiary">
                  最近配置更新时间: {item.core_source.updated_at || options[0]?.updated_at || '-'}
                </Typography.Text>

                {item.latest_job ? (
                  <Typography.Text type="tertiary">
                    最近任务: {item.latest_job.job_type} / {item.latest_job.status} / {item.latest_job.triggered_at}
                  </Typography.Text>
                ) : (
                  <Typography.Text type="tertiary">暂无同步任务记录</Typography.Text>
                )}
              </Space>
            </Card>
          );
        })
      )}

      <Card title="健康系统单次回填任务（backfill_once）" shadows="hover">
        {!healthSource?.core_source.connector_code ? (
          <Typography.Text type="warning">请先为健康系统设置核心数据源，再触发回填任务。</Typography.Text>
        ) : !writable ? (
          <Typography.Text type="warning">当前账号无 `system_source.write` 权限，不能触发回填任务。</Typography.Text>
        ) : (
          <Space vertical align="start" style={{ width: '100%' }}>
            <Typography.Text type="tertiary">
              请输入东八区时间（示例：2026-02-01T00:00:00+08:00）。
            </Typography.Text>

            <div className="inline-row wrap">
              <Input
                value={backfillStartAt}
                onChange={setBackfillStartAt}
                style={{ width: 320 }}
                placeholder="backfill_start_at"
              />
              <Input
                value={backfillEndAt}
                onChange={setBackfillEndAt}
                style={{ width: 320 }}
                placeholder="backfill_end_at"
              />
              <Button theme="solid" type="primary" onClick={() => void handleCreateBackfill()}>
                触发手动回填
              </Button>
            </div>

            <Table
              pagination={false}
              dataSource={healthJobsQuery.data?.items ?? []}
              rowKey="job_id"
              columns={[
                { title: 'Job ID', dataIndex: 'job_id', width: 220 },
                { title: '类型', dataIndex: 'job_type', width: 120 },
                { title: '状态', dataIndex: 'status', width: 100 },
                { title: '触发时间', dataIndex: 'triggered_at', width: 220 },
                { title: '开始', dataIndex: 'started_at', width: 220 },
                { title: '结束', dataIndex: 'finished_at', width: 220 },
                { title: '错误', dataIndex: 'error_message' },
              ]}
            />
          </Space>
        )}
      </Card>
    </Space>
  );
}
