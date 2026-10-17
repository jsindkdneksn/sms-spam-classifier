"""Credential routing must follow the selected storage, even with both tokens present."""

import pytest

from scripts import pull_artifacts


@pytest.mark.parametrize("remote", ["azure", "dagshub"])
@pytest.mark.parametrize("quote", ["", "'"])
def test_credentials_follow_remote_not_token_presence(tmp_path, monkeypatch, remote, quote):
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".dvc").mkdir()
    (tmp_path / ".dvc/config").write_text(
        f'[{quote}remote "azure"{quote}]\nurl = azure://container/team\n'
        f'[{quote}remote "dagshub"{quote}]\nurl = https://dagshub.com/team/repo.dvc\n',
        encoding="utf-8",
    )
    (tmp_path / "models").mkdir()
    (tmp_path / "models/release.dvc").touch()
    monkeypatch.setenv("DVC_REMOTE", remote)
    monkeypatch.setenv("DAGSHUB_TOKEN", "test-dagshub-secret")
    monkeypatch.setenv("DAGSHUB_USERNAME", "team")
    monkeypatch.setenv("AZURE_SAS_TOKEN", "test-azure-secret")
    monkeypatch.setenv("AZURE_STORAGE_ACCOUNT", "testaccount")
    calls = []
    monkeypatch.setattr(pull_artifacts, "dvc", lambda *args: calls.append(args))
    pull_artifacts.pull()
    joined = repr(calls)
    if remote == "azure":
        assert "test-azure-secret" in joined
        assert "test-dagshub-secret" not in joined
        assert "basic" not in joined
    else:
        assert "test-dagshub-secret" in joined
        assert "test-azure-secret" not in joined
    assert calls[-1] == ("pull", "models/release.dvc", "-r", remote)
