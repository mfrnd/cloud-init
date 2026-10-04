# This file is part of cloud-init. See LICENSE file for license information.

import logging

import pytest

from tests.unittests.helpers import get_distro, mock

M_PATH = "cloudinit.distros.bsd."


@pytest.fixture(params=["freebsd", "netbsd", "dragonflybsd"])
def distro(request):
    return get_distro(request.param)


@mock.patch(M_PATH + "bsd_utils.set_rc_config_value")
@mock.patch(M_PATH + "bsd_utils.get_rc_config_value")
class TestHostname:
    def test_previous_hostname_is_its_own_file(
        self, m_get_rc, m_set_rc, distro, tmp_path
    ):
        prev_fn = str(tmp_path / "previous-hostname")
        distro._write_hostname("myhost", prev_fn)
        assert distro._read_hostname(prev_fn) == "myhost"
        m_get_rc.assert_not_called()
        m_set_rc.assert_not_called()

    def test_system_hostname_is_in_rc_conf(self, m_get_rc, m_set_rc, distro):
        m_get_rc.return_value = "myhost"
        assert distro._read_system_hostname() == ("/etc/rc.conf", "myhost")
        distro._write_hostname("newhost", "/etc/rc.conf")
        m_set_rc.assert_called_once_with(
            "hostname", "newhost", fn="/etc/rc.conf"
        )

    def test_update_hostname_keeps_a_user_maintained_hostname(
        self, m_get_rc, m_set_rc, distro, tmp_path, caplog
    ):
        """A hostname the user changed after cloud-init set it is kept."""
        prev_fn = tmp_path / "previous-hostname"
        prev_fn.write_text("cloudhost\n")
        m_get_rc.return_value = "userhost"
        with caplog.at_level(logging.INFO):
            distro.update_hostname("cloudhost", "cloudhost", str(prev_fn))
        assert "assuming user maintained hostname" in caplog.text
        m_set_rc.assert_not_called()

    @mock.patch("cloudinit.distros.subp.subp")
    def test_update_hostname_follows_a_changed_hostname(
        self, m_subp, m_get_rc, m_set_rc, distro, tmp_path
    ):
        """A hostname cloud-init still manages follows the datasource."""
        prev_fn = tmp_path / "previous-hostname"
        prev_fn.write_text("oldhost\n")
        m_get_rc.return_value = "oldhost"
        distro.update_hostname("newhost", "newhost", str(prev_fn))
        assert prev_fn.read_text() == "newhost\n"
        m_set_rc.assert_called_once_with(
            "hostname", "newhost", fn="/etc/rc.conf"
        )
        m_subp.assert_called_once_with(["hostname", "newhost"])
