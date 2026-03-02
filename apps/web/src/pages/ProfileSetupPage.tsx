import { FormEvent, useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button, Card, Input, InputNumber, Space, Typography } from '@douyinfe/semi-ui';
import { useQuery } from '@tanstack/react-query';

import { useAuth } from '../contexts/AuthContext';
import { getMyProfile, updateMyProfile } from '../services/api';
import { ApiError } from '../services/http';

export function ProfileSetupPage() {
  const navigate = useNavigate();
  const { accessToken, reloadMe, user } = useAuth();

  const profileQuery = useQuery({
    queryKey: ['profile-me', accessToken],
    queryFn: () => getMyProfile(accessToken ?? ''),
    enabled: Boolean(accessToken),
  });

  const [displayName, setDisplayName] = useState('');
  const [timezone, setTimezone] = useState('Asia/Shanghai');
  const [gender, setGender] = useState('');
  const [birthDate, setBirthDate] = useState('');
  const [heightCm, setHeightCm] = useState<number | undefined>(undefined);
  const [weightKg, setWeightKg] = useState<number | undefined>(undefined);
  const [submitting, setSubmitting] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');

  useEffect(() => {
    if (!profileQuery.data) {
      return;
    }
    setDisplayName(profileQuery.data.display_name ?? '');
    setTimezone(profileQuery.data.timezone ?? 'Asia/Shanghai');
    setGender(profileQuery.data.gender ?? '');
    setBirthDate(profileQuery.data.birth_date ?? '');
    setHeightCm(profileQuery.data.height_cm ?? undefined);
    setWeightKg(profileQuery.data.weight_kg ?? undefined);
  }, [profileQuery.data]);

  useEffect(() => {
    if (user?.profile_completed) {
      navigate('/app/health/overview', { replace: true });
    }
  }, [navigate, user]);

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!accessToken) {
      return;
    }

    setErrorMessage('');
    if (!displayName.trim()) {
      setErrorMessage('请填写昵称');
      return;
    }

    setSubmitting(true);
    try {
      await updateMyProfile(accessToken, {
        display_name: displayName.trim(),
        timezone: timezone.trim() || 'Asia/Shanghai',
        gender: gender.trim() || null,
        birth_date: birthDate.trim() || null,
        height_cm: typeof heightCm === 'number' ? heightCm : null,
        weight_kg: typeof weightKg === 'number' ? weightKg : null,
      });
      await reloadMe();
      navigate('/app/health/overview', { replace: true });
    } catch (error) {
      if (error instanceof ApiError) {
        setErrorMessage(error.message);
      } else {
        setErrorMessage('保存失败，请稍后重试。');
      }
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="profile-setup-page">
      <Card className="profile-setup-card" shadows="always">
        <Typography.Title heading={3} style={{ marginBottom: 4 }}>
          首次登录资料维护
        </Typography.Title>
        <Typography.Text type="tertiary">保存资料后才可进入业务页面。</Typography.Text>

        <form className="profile-form" onSubmit={handleSubmit}>
          <Space vertical align="start" style={{ width: '100%' }}>
            <label className="form-label" htmlFor="profile-display-name">
              昵称（必填）
            </label>
            <Input
              id="profile-display-name"
              value={displayName}
              onChange={setDisplayName}
              placeholder="请输入昵称"
              size="large"
            />

            <label className="form-label" htmlFor="profile-timezone">
              时区（必填）
            </label>
            <Input
              id="profile-timezone"
              value={timezone}
              onChange={setTimezone}
              placeholder="Asia/Shanghai"
              size="large"
            />

            <label className="form-label" htmlFor="profile-gender">
              性别（可选）
            </label>
            <Input
              id="profile-gender"
              value={gender}
              onChange={setGender}
              placeholder="male / female / other"
              size="large"
            />

            <label className="form-label" htmlFor="profile-birth-date">
              出生日期（可选）
            </label>
            <Input
              id="profile-birth-date"
              value={birthDate}
              onChange={setBirthDate}
              placeholder="YYYY-MM-DD"
              size="large"
            />

            <label className="form-label" htmlFor="profile-height">
              身高 cm（可选）
            </label>
            <InputNumber
              id="profile-height"
              value={heightCm}
              onChange={(value) => setHeightCm(typeof value === 'number' ? value : undefined)}
              style={{ width: '100%' }}
              min={30}
              max={300}
            />

            <label className="form-label" htmlFor="profile-weight">
              体重 kg（可选）
            </label>
            <InputNumber
              id="profile-weight"
              value={weightKg}
              onChange={(value) => setWeightKg(typeof value === 'number' ? value : undefined)}
              style={{ width: '100%' }}
              min={1}
              max={700}
            />

            {errorMessage ? <Typography.Text type="danger">{errorMessage}</Typography.Text> : null}

            <Button
              htmlType="submit"
              theme="solid"
              type="primary"
              size="large"
              loading={submitting || profileQuery.isLoading}
              style={{ width: '100%' }}
            >
              保存并进入业务页
            </Button>
          </Space>
        </form>
      </Card>
    </div>
  );
}
