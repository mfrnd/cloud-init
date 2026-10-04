# This file is part of cloud-init. See LICENSE file for license information.

from tests.unittests.helpers import get_distro, mock

M_PATH = "cloudinit.distros.aosc."


class TestAOSC:
    def test_get_distro(self):
        distro = get_distro("aosc")
        assert distro.osfamily == "aosc"


@mock.patch(M_PATH + "subp.subp")
class TestHostname:
    def test_previous_hostname_is_its_own_file(self, m_subp, tmp_path):
        distro = get_distro("aosc")
        prev_fn = str(tmp_path / "previous-hostname")
        distro._write_hostname("myhost", prev_fn)
        assert distro._read_hostname(prev_fn) == "myhost"
        m_subp.assert_not_called()

    def test_system_hostname_is_set_with_hostnamectl(self, m_subp):
        distro = get_distro("aosc")
        distro._write_hostname("myhost", "/etc/hostname")
        m_subp.assert_called_once_with(
            ["hostnamectl", "set-hostname", "myhost"]
        )

    def test_update_hostname_creates_a_missing_record_only(
        self, m_subp, tmp_path
    ):
        """A missing record is created without touching the system
        hostname, which may be one the user set."""
        distro = get_distro("aosc")
        m_subp.return_value = ("userhost\n", "")
        prev_fn = tmp_path / "previous-hostname"
        distro.update_hostname("cloudhost", "cloudhost", str(prev_fn))
        assert distro._read_hostname(str(prev_fn)) == "cloudhost"
        m_subp.assert_called_once_with(["hostname"])
