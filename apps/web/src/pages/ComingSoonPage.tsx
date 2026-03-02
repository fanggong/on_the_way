import { Card, Typography } from '@douyinfe/semi-ui';

interface Props {
  title: string;
}

export function ComingSoonPage({ title }: Props) {
  return (
    <Card title={title} shadows="hover">
      <Typography.Title heading={4}>开发中</Typography.Title>
      <Typography.Text type="tertiary">本版本仅开放健康模块能力，其他模块将在后续版本逐步上线。</Typography.Text>
    </Card>
  );
}
