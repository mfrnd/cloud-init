# This file is part of cloud-init. See LICENSE file for license information.

import logging

import pytest

from tests.unittests.helpers import get_distro, mock

M_PATH = "cloudinit.distros.openbsd."


class TestOpenBSD:
    @mock.patch(M_PATH + "subp.subp")
    def test_add_user(self, m_subp):
        distro = get_distro("openbsd")
        distro.add_user("me2", groups=[], uid=1234, default=False)
        assert [
            mock.call(
                ["useradd", "-m", "me2"], logstring=["useradd", "-m", "me2"]
            )
        ] == m_subp.call_args_list

    def test_unlock_passwd(self, caplog):
        distro = get_distro("openbsd")
        distro.unlock_passwd("me2")
        assert (
            "OpenBSD password lock is not reversible, "
            "ignoring unlock for user me2" in caplog.text
        )


class TestHostname:
    @pytest.fixture
    def myname(self, tmp_path):
        return tmp_path / "myname"

    @pytest.fixture
    def distro(self, myname):
        distro = get_distro("openbsd")
        distro.hostname_conf_fn = str(myname)
        return distro

    def test_system_hostname_is_read_without_the_newline(self, distro, myname):
        myname.write_text("myhost\n")
        assert distro._read_system_hostname() == (str(myname), "myhost")

    def test_previous_hostname_is_its_own_file(self, distro, myname, tmp_path):
        myname.write_text("myhost\n")
        prev_fn = str(tmp_path / "previous-hostname")
        distro._write_hostname("prevhost", prev_fn)
        assert distro._read_hostname(prev_fn) == "prevhost"
        assert myname.read_text() == "myhost\n"

    def test_update_hostname_keeps_a_user_maintained_hostname(
        self, distro, myname, tmp_path, caplog
    ):
        """A hostname the user changed after cloud-init set it is kept."""
        myname.write_text("userhost\n")
        prev_fn = tmp_path / "previous-hostname"
        prev_fn.write_text("cloudhost\n")
        with caplog.at_level(logging.INFO):
            distro.update_hostname("cloudhost", "cloudhost", str(prev_fn))
        assert "assuming user maintained hostname" in caplog.text
        assert myname.read_text() == "userhost\n"

    @mock.patch("cloudinit.distros.subp.subp")
    def test_update_hostname_follows_a_changed_hostname(
        self, m_subp, distro, myname, tmp_path
    ):
        """A hostname cloud-init still manages follows the datasource."""
        myname.write_text("oldhost\n")
        prev_fn = tmp_path / "previous-hostname"
        prev_fn.write_text("oldhost\n")
        distro.update_hostname("newhost", "newhost", str(prev_fn))
        assert myname.read_text() == "newhost\n"
        assert prev_fn.read_text() == "newhost\n"
        m_subp.assert_called_once_with(["hostname", "newhost"])
