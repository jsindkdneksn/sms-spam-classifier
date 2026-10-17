"""Temporary negative control for branch protection. Never merge this file."""


def test_branch_protection_negative_control():
    assert 1 == 2, "Intentional failure to verify required CI blocks merging"
