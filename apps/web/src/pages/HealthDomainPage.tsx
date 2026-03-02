import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Button, Card, Input, Space, Table, Typography } from '@douyinfe/semi-ui';

import { useAuth } from '../contexts/AuthContext';
import { queryHealthDomainMetrics } from '../services/api';

function todayDateText(): string {
  return new Date().toISOString().slice(0, 10);
}

function sevenDaysAgoText(): string {
  const now = new Date();
  now.setDate(now.getDate() - 6);
  return now.toISOString().slice(0, 10);
}

export function HealthDomainPage() {
  const { accessToken } = useAuth();

  const [startDate, setStartDate] = useState(sevenDaysAgoText());
  const [endDate, setEndDate] = useState(todayDateText());
  const [metricName, setMetricName] = useState('');
  const [accountRef, setAccountRef] = useState('');
  const [submittedAt, setSubmittedAt] = useState(0);

  const domainQuery = useQuery({
    queryKey: ['health-domain-metrics', accessToken, startDate, endDate, metricName, accountRef, submittedAt],
    queryFn: () =>
      queryHealthDomainMetrics(accessToken ?? '', {
        start_date: startDate,
        end_date: endDate,
        metric_name: metricName || undefined,
        account_ref: accountRef || undefined,
        page: 1,
        page_size: 100,
      }),
    enabled: Boolean(accessToken && submittedAt > 0),
  });

  return (
    <Space vertical spacing="medium" style={{ width: '100%' }}>
      <Card title="Domain 数据查询" shadows="hover">
        <Space wrap>
          <Input value={startDate} onChange={setStartDate} style={{ width: 160 }} placeholder="start_date" />
          <Input value={endDate} onChange={setEndDate} style={{ width: 160 }} placeholder="end_date" />
          <Input value={metricName} onChange={setMetricName} style={{ width: 220 }} placeholder="metric_name (可选)" />
          <Input value={accountRef} onChange={setAccountRef} style={{ width: 220 }} placeholder="account_ref (可选)" />
          <Button theme="solid" type="primary" onClick={() => setSubmittedAt(Date.now())}>
            查询
          </Button>
        </Space>

        <Typography.Text type="tertiary" style={{ display: 'block', marginTop: 12 }}>
          字段来源：domain_health.health_metric_daily_fact
        </Typography.Text>
      </Card>

      <Card title="查询结果" shadows="hover">
        <Table
          rowKey="domain_metric_row_id"
          pagination={{ pageSize: 20 }}
          dataSource={domainQuery.data?.items ?? []}
          columns={[
            { title: 'metric_date', dataIndex: 'metric_date', width: 130 },
            { title: 'metric_name', dataIndex: 'metric_name', width: 220 },
            { title: 'metric_value_num', dataIndex: 'metric_value_num', width: 140 },
            { title: 'quality_flag', dataIndex: 'quality_flag', width: 130 },
            { title: 'account_ref', dataIndex: 'account_ref', width: 140 },
            { title: 'latest_ingested_at', dataIndex: 'latest_ingested_at' },
          ]}
          loading={domainQuery.isFetching}
        />
      </Card>
    </Space>
  );
}
