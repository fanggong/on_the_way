import { type CSSProperties, type ReactNode, useMemo } from 'react';
import { Outlet, useLocation, useNavigate } from 'react-router-dom';
import { Button, Layout, Nav, Tag, Typography } from '@douyinfe/semi-ui';

import { useAuth } from '../contexts/AuthContext';

const { Header, Sider, Content } = Layout;

const siderStyle: CSSProperties = {
  background: 'linear-gradient(180deg, #0f172a 0%, #111827 100%)',
  borderRight: '1px solid rgba(148, 163, 184, 0.25)',
};

export function AppFrame() {
  const navigate = useNavigate();
  const location = useLocation();
  const { user, logout, hasPermission } = useAuth();
  const canReadMart = hasPermission('health.mart.read');
  const canReadDomain = hasPermission('health.domain.read');

  const navItems = useMemo(() => {
    const list: Array<{ key: string; text: string; icon?: ReactNode }> = [];

    if (canReadMart) {
      list.push(
        { key: '/app/health/overview', text: '健康总览' },
        { key: '/app/health/connectors', text: '健康连接器' },
        { key: '/app/health/mart', text: '健康 Mart 展示' },
      );
    }

    if (canReadDomain) {
      list.push({ key: '/app/health/domain', text: '健康 Domain 查询' });
    }

    list.push(
      { key: '/app/system-sources', text: '系统数据源管理' },
      { key: '/app/time', text: '时间' },
      { key: '/app/income', text: '收入' },
      { key: '/app/finance', text: '财务' },
      { key: '/app/ability', text: '能力' },
      { key: '/app/relationship', text: '关系' },
      { key: '/app/life', text: '生活' },
      { key: '/app/security', text: '保障' },
    );

    return list;
  }, [canReadDomain, canReadMart]);

  const selectedKey = useMemo(() => {
    const item = navItems.find((candidate) => location.pathname.startsWith(candidate.key));
    if (item) {
      return item.key;
    }
    return navItems[0]?.key ?? '/app/time';
  }, [location.pathname, navItems]);

  return (
    <Layout className="app-frame">
      <Sider style={siderStyle}>
        <div className="sider-header">
          <Typography.Title heading={4} style={{ color: '#f8fafc', margin: 0 }}>
            On The Way
          </Typography.Title>
          <Typography.Text style={{ color: '#94a3b8' }}>Web Admin v0.4.0</Typography.Text>
        </div>
        <Nav
          style={{ height: 'calc(100vh - 92px)', backgroundColor: 'transparent' }}
          selectedKeys={[selectedKey]}
          onSelect={(data) => {
            navigate(String(data.itemKey));
          }}
          footer={{
            collapseButton: false,
          }}
        >
          {navItems.map((item) => (
            <Nav.Item itemKey={item.key} text={item.text} icon={item.icon} key={item.key} />
          ))}
        </Nav>
      </Sider>

      <Layout>
        <Header className="app-header">
          <div>
            <Typography.Title heading={5} style={{ margin: 0 }}>
              {selectedKey === '/app/system-sources' ? '系统数据源管理' : '业务控制台'}
            </Typography.Title>
            <Typography.Text type="tertiary">统一账号、权限、连接器与健康数据查询入口</Typography.Text>
          </div>

          <div className="header-user-meta">
            <Tag color="blue">{user?.roles.join(', ') || '-'}</Tag>
            <Tag color="cyan">{user?.email ?? '-'}</Tag>
            <Button onClick={() => void logout()} theme="borderless" type="danger">
              退出登录
            </Button>
          </div>
        </Header>

        <Content className="app-content">
          <Outlet />
        </Content>
      </Layout>
    </Layout>
  );
}
