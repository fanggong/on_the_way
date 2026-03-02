import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Button, Card, Input, Space, Table, Tabs, Typography } from '@douyinfe/semi-ui';

import { useAuth } from '../contexts/AuthContext';
import {
  queryHealthMartActivityTopics,
  queryHealthMartMetricSummary,
  queryHealthMartOverview,
} from '../services/api';

function todayDateText(): string {
  return new Date().toISOString().slice(0, 10);
}

function sevenDaysAgoText(): string {
  const now = new Date();
  now.setDate(now.getDate() - 6);
  return now.toISOString().slice(0, 10);
}

export function HealthMartPage() {
  const { accessToken } = useAuth();
  const [startDate, setStartDate] = useState(sevenDaysAgoText());
  const [endDate, setEndDate] = useState(todayDateText());
  const [accountRef, setAccountRef] = useState('');
  const [submittedAt, setSubmittedAt] = useState(0);

  const overviewQuery = useQuery({
    queryKey: ['health-mart-overview', accessToken, startDate, endDate, accountRef, submittedAt],
    queryFn: () =>
      queryHealthMartOverview(accessToken ?? '', {
        start_date: startDate,
        end_date: endDate,
        account_ref: accountRef || undefined,
        page: 1,
        page_size: 100,
      }),
    enabled: Boolean(accessToken && submittedAt > 0),
  });

  const summaryQuery = useQuery({
    queryKey: ['health-mart-summary', accessToken, startDate, endDate, accountRef, submittedAt],
    queryFn: () =>
      queryHealthMartMetricSummary(accessToken ?? '', {
        start_date: startDate,
        end_date: endDate,
        account_ref: accountRef || undefined,
        page: 1,
        page_size: 100,
      }),
    enabled: Boolean(accessToken && submittedAt > 0),
  });

  const activityQuery = useQuery({
    queryKey: ['health-mart-activity', accessToken, startDate, endDate, accountRef, submittedAt],
    queryFn: () =>
      queryHealthMartActivityTopics(accessToken ?? '', {
        start_date: startDate,
        end_date: endDate,
        account_ref: accountRef || undefined,
        page: 1,
        page_size: 100,
      }),
    enabled: Boolean(accessToken && submittedAt > 0),
  });

  return (
    <Space vertical spacing="medium" style={{ width: '100%' }}>
      <Card title="Mart 数据展示" shadows="hover">
        <Space wrap>
          <Input value={startDate} onChange={setStartDate} style={{ width: 160 }} placeholder="start_date" />
          <Input value={endDate} onChange={setEndDate} style={{ width: 160 }} placeholder="end_date" />
          <Input value={accountRef} onChange={setAccountRef} style={{ width: 220 }} placeholder="account_ref (可选)" />
          <Button theme="solid" type="primary" onClick={() => setSubmittedAt(Date.now())}>
            查询
          </Button>
        </Space>

        <Typography.Text type="tertiary" style={{ display: 'block', marginTop: 12 }}>
          数据来源：mart.health_daily_overview / mart.health_metric_daily_summary / mart.health_activity_topic_daily
        </Typography.Text>
      </Card>

      <Card>
        <Tabs type="line" defaultActiveKey="overview">
          <Tabs.TabPane tab="日级概览" itemKey="overview">
            <Table
              pagination={{ pageSize: 20 }}
              dataSource={overviewQuery.data?.items ?? []}
              loading={overviewQuery.isFetching}
              rowKey={(record) => `${record?.account_ref ?? 'unknown'}-${record?.stat_date ?? 'unknown'}`}
              columns={[
                { title: 'stat_date', dataIndex: 'stat_date', width: 130 },
                { title: 'sleep_duration_min', dataIndex: 'sleep_duration_min', width: 160 },
                { title: 'resting_hr_bpm', dataIndex: 'resting_hr_bpm', width: 140 },
                { title: 'steps_count', dataIndex: 'steps_count', width: 120 },
                { title: 'active_kcal', dataIndex: 'active_kcal', width: 120 },
                { title: 'quality_issue_count', dataIndex: 'quality_issue_count', width: 150 },
              ]}
            />
          </Tabs.TabPane>

          <Tabs.TabPane tab="指标汇总" itemKey="metric-summary">
            <Table
              pagination={{ pageSize: 20 }}
              dataSource={summaryQuery.data?.items ?? []}
              loading={summaryQuery.isFetching}
              rowKey={(record) =>
                `${record?.account_ref ?? 'unknown'}-${record?.stat_date ?? 'unknown'}-${
                  record?.metric_name ?? 'unknown'
                }`
              }
              columns={[
                { title: 'stat_date', dataIndex: 'stat_date', width: 130 },
                { title: 'metric_name', dataIndex: 'metric_name', width: 220 },
                { title: 'value_avg', dataIndex: 'value_avg', width: 130 },
                { title: 'value_min', dataIndex: 'value_min', width: 130 },
                { title: 'value_max', dataIndex: 'value_max', width: 130 },
                { title: 'sample_count', dataIndex: 'sample_count', width: 130 },
              ]}
            />
          </Tabs.TabPane>

          <Tabs.TabPane tab="活动主题" itemKey="activity-topic">
            <Table
              pagination={{ pageSize: 20 }}
              dataSource={activityQuery.data?.items ?? []}
              loading={activityQuery.isFetching}
              rowKey={(record) =>
                `${record?.account_ref ?? 'unknown'}-${record?.stat_date ?? 'unknown'}-${
                  record?.activity_type ?? 'unknown'
                }`
              }
              columns={[
                { title: 'stat_date', dataIndex: 'stat_date', width: 130 },
                { title: 'activity_type', dataIndex: 'activity_type', width: 200 },
                { title: 'activity_count', dataIndex: 'activity_count', width: 130 },
                { title: 'duration_seconds_sum', dataIndex: 'duration_seconds_sum', width: 170 },
                { title: 'distance_meters_sum', dataIndex: 'distance_meters_sum', width: 170 },
                { title: 'calories_kcal_sum', dataIndex: 'calories_kcal_sum', width: 150 },
              ]}
            />
          </Tabs.TabPane>
        </Tabs>
      </Card>
    </Space>
  );
}
