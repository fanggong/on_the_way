import { useEffect, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Button, Card, Input, InputNumber, Space, Switch, Toast, Typography } from '@douyinfe/semi-ui';

import { useAuth } from '../contexts/AuthContext';
import {
  getConnectorHealthSummary,
  getHealthConnectorConfig,
  updateHealthConnectorConfig,
} from '../services/api';

export function HealthConnectorConfigPage() {
  const { accessToken, hasPermission } = useAuth();
  const writable = hasPermission('health.connector.write');

  const configQuery = useQuery({
    queryKey: ['health-connector-config', accessToken],
    queryFn: () => getHealthConnectorConfig(accessToken ?? ''),
    enabled: Boolean(accessToken),
  });
  const connectorHealthQuery = useQuery({
    queryKey: ['health-connector-health'],
    queryFn: () => getConnectorHealthSummary(),
  });

  const [fetchWindowDays, setFetchWindowDays] = useState(3);
  const [backfillDays, setBackfillDays] = useState(10);
  const [timezone, setTimezone] = useState('Asia/Shanghai');
  const [isCn, setIsCn] = useState(true);

  useEffect(() => {
    if (!configQuery.data) {
      return;
    }
    setFetchWindowDays(configQuery.data.GARMIN_FETCH_WINDOW_DAYS);
    setBackfillDays(configQuery.data.GARMIN_BACKFILL_DAYS);
    setTimezone(configQuery.data.GARMIN_TIMEZONE);
    setIsCn(configQuery.data.GARMIN_IS_CN);
  }, [configQuery.data]);

  const handleSave = async () => {
    if (!accessToken || !writable) {
      return;
    }

    try {
      await updateHealthConnectorConfig(accessToken, {
        GARMIN_FETCH_WINDOW_DAYS: fetchWindowDays,
        GARMIN_BACKFILL_DAYS: backfillDays,
        GARMIN_TIMEZONE: timezone,
        GARMIN_IS_CN: isCn,
      });
      Toast.success('健康连接器配置已更新');
      await configQuery.refetch();
    } catch (error) {
      Toast.error(error instanceof Error ? error.message : '保存失败');
    }
  };

  return (
    <Card title="健康连接器配置" shadows="hover">
      <Space vertical align="start" style={{ width: '100%' }}>
        <Typography.Text type="tertiary">
          自动同步频率由“系统数据源管理”统一维护，本页面仅维护 Garmin 连接器白名单配置。
        </Typography.Text>

        <Card title="连接器运行状态" style={{ width: '100%' }}>
          <Space vertical align="start" style={{ width: '100%' }}>
            <Typography.Text>
              最近执行状态：{connectorHealthQuery.data?.last_status ?? '-'}
            </Typography.Text>
            <Typography.Text>
              最近执行时间：{connectorHealthQuery.data?.last_run_at ?? '-'}
            </Typography.Text>
            <Typography.Text>
              累计成功次数：{connectorHealthQuery.data?.success_count ?? 0}
            </Typography.Text>
            <Typography.Text>
              累计失败次数：{connectorHealthQuery.data?.failure_count ?? 0}
            </Typography.Text>
          </Space>
        </Card>

        <div className="inline-row wrap">
          <Typography.Text>GARMIN_FETCH_WINDOW_DAYS</Typography.Text>
          <InputNumber
            value={fetchWindowDays}
            min={1}
            max={90}
            onChange={(value) => setFetchWindowDays(typeof value === 'number' ? value : fetchWindowDays)}
            disabled={!writable}
          />
        </div>

        <div className="inline-row wrap">
          <Typography.Text>GARMIN_BACKFILL_DAYS</Typography.Text>
          <InputNumber
            value={backfillDays}
            min={1}
            max={180}
            onChange={(value) => setBackfillDays(typeof value === 'number' ? value : backfillDays)}
            disabled={!writable}
          />
        </div>

        <div className="inline-row wrap">
          <Typography.Text>GARMIN_TIMEZONE</Typography.Text>
          <Input value={timezone} onChange={setTimezone} style={{ width: 280 }} disabled={!writable} />
        </div>

        <div className="inline-row wrap">
          <Typography.Text>GARMIN_IS_CN</Typography.Text>
          <Switch checked={isCn} onChange={(checked) => setIsCn(checked)} disabled={!writable} />
        </div>

        <Button theme="solid" type="primary" onClick={() => void handleSave()} disabled={!writable}>
          保存配置
        </Button>

        {!writable ? (
          <Typography.Text type="warning">当前账号无 `health.connector.write` 权限，仅可查看。</Typography.Text>
        ) : null}
      </Space>
    </Card>
  );
}
