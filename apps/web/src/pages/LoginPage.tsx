import { FormEvent, useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Button, Card, Input, Space, Typography } from '@douyinfe/semi-ui';

import { ApiError } from '../services/http';
import { useAuth } from '../contexts/AuthContext';

export function LoginPage() {
  const navigate = useNavigate();
  const { user, bootstrapping, login } = useAuth();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');

  useEffect(() => {
    if (bootstrapping) {
      return;
    }
    if (user?.profile_completed) {
      navigate('/app/health/overview', { replace: true });
    } else if (user) {
      navigate('/app/profile/setup', { replace: true });
    }
  }, [bootstrapping, navigate, user]);

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setErrorMessage('');
    setSubmitting(true);

    try {
      await login(email.trim(), password);
      navigate('/app/health/overview', { replace: true });
    } catch (error) {
      if (error instanceof ApiError) {
        setErrorMessage(error.message);
      } else {
        setErrorMessage('登录失败，请稍后重试。');
      }
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="auth-page">
      <Card className="auth-card" shadows="always">
        <Typography.Title heading={3} style={{ marginBottom: 4 }}>
          登录 On The Way
        </Typography.Title>
        <Typography.Text type="tertiary">邮箱 + 密码登录，首次登录将进入资料完善流程。</Typography.Text>

        <form onSubmit={handleSubmit} className="auth-form">
          <Space vertical align="start" style={{ width: '100%' }}>
            <label className="form-label" htmlFor="email-input">
              邮箱
            </label>
            <Input
              id="email-input"
              value={email}
              onChange={setEmail}
              placeholder="user@example.com"
              size="large"
            />

            <label className="form-label" htmlFor="password-input">
              密码
            </label>
            <Input
              id="password-input"
              mode="password"
              value={password}
              onChange={setPassword}
              placeholder="请输入密码"
              size="large"
            />

            {errorMessage ? <Typography.Text type="danger">{errorMessage}</Typography.Text> : null}

            <Button htmlType="submit" theme="solid" size="large" loading={submitting} style={{ width: '100%' }}>
              登录
            </Button>
          </Space>
        </form>

        <Typography.Text type="tertiary">
          还没有账号？<Link to="/auth/register">去注册</Link>
        </Typography.Text>
      </Card>
    </div>
  );
}
