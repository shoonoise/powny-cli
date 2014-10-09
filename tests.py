import unittest
import vcr
from click.testing import CliRunner
from pownycli import client, settings


test_vcr = vcr.VCR(cassette_library_dir="fixtures")


class TestPownyCommand(unittest.TestCase):
    def setUp(self):
        self.runner = CliRunner()
        self.api_url = "http://localhost"
        settings.Settings.config = {'powny_api_url': self.api_url}

    def test_powny_cluster_info(self):
        with test_vcr.use_cassette("powny_cluster_info.yaml") as cass:
            result = self.runner.invoke(client.cluster_info)

            self.assertEqual(cass.requests[0].uri, "{}/v1/system/state".format(self.api_url))
            self.assertEqual(result.exit_code, 0)

    def test_powny_job_list(self):
        with test_vcr.use_cassette("powny_job_list.yaml") as cass:
            result = self.runner.invoke(client.job, ["list"])
            self.assertEqual(cass.requests[0].uri, "{}/v1/jobs".format(self.api_url))
            self.assertEqual(result.exit_code, 0)

    def test_powny_kill_job(self):
        job_id = "baca2a09-e510-4851-8a05-2f732582249d"
        with test_vcr.use_cassette("powny_kill_job.yaml") as cass:
            result = self.runner.invoke(client.job, ["kill", job_id])

            self.assertEqual(cass.requests[0].uri,
                             "{}/v1/jobs/{}".format(self.api_url, job_id))
            self.assertEqual(result.exit_code, 0)

    def test_powny_send_event(self):
        with test_vcr.use_cassette("powny_send_event.yaml") as cass:
            result = self.runner.invoke(client.send_event, ["http://host.net", "GNS", "CRIT"])
            self.assertEqual(cass.requests[0].uri,
                             self.api_url + "/v1/jobs")
            self.assertEqual(result.exit_code, 0)
