import unittest
import vcr
from click.testing import CliRunner
from gnscli import client
from gnscli import gnsapi


test_vcr = vcr.VCR(cassette_library_dir="fixtures")


class TestGNSCommand(unittest.TestCase):
    def setUp(self):
        self.runner = CliRunner()
        self.api_url = "http://localhost:7887/api"

    def test_gns_cluster_info(self):
        with test_vcr.use_cassette("gns_cluster_info.yaml") as cass:
            result = self.runner.invoke(client.gns, ["--api-url={}".format(self.api_url), "cluster-info"])

            self.assertEqual(cass.requests[0].uri, "{}/rest/v1/system/state".format(self.api_url))
            self.assertEqual(result.exit_code, 0)

    def test_gns_job_list(self):
        with test_vcr.use_cassette("gns_job_list.yaml") as cass:
            result = self.runner.invoke(client.gns, ["--api-url={}".format(self.api_url), "job-list"])
            self.assertEqual(cass.requests[0].uri, "{}/rest/v1/jobs".format(self.api_url))
            self.assertEqual(result.exit_code, 0)

    def test_gns_kill_job(self):
        job_id = "87311816-d0ad-4668-b1cd-6e095d9d01da"
        with test_vcr.use_cassette("gns_kill_job.yaml") as cass:
            result = self.runner.invoke(client.gns,
                                        ["--api-url={}".format(self.api_url),
                                         "kill-job", job_id])
            self.assertEqual(cass.requests[0].uri,
                             "{}/rest/v1/jobs/{}".format(self.api_url, job_id))
            self.assertEqual(result.exit_code, 0)

    def test_gns_send_event(self):
        with test_vcr.use_cassette("gns_send_event.yaml") as cass:
            result = self.runner.invoke(client.gns, ["--api-url={}".format(self.api_url),
                                                     "send-event", "http://host.net", "GNS", "CRIT"])
            self.assertEqual(cass.requests[0].uri,
                             self.api_url + "/rest/v1/jobs")
            self.assertEqual(result.exit_code, 0)


class TestGNSAPI(unittest.TestCase):

    def setUp(self):
        self.api_url = "http://gns-testing.haze.yandex.net:7887/api"

    def test_get_header(self):
        with test_vcr.use_cassette("gns_get_head.yaml") as cass:
            gnsapi.get_header(self.api_url)
            self.assertEqual(cass.requests[0].uri, self.api_url + "/rest/v1/rules/head")

    def test_set_head(self):
        with test_vcr.use_cassette("gns_set_head.yaml") as cass:
            gnsapi.set_header("http://gns-testing.haze.yandex.net:7887/api",
                              "2238e6636063b57b541c0f1799596e1617dec489")
            self.assertEqual(cass.requests[0].uri, self.api_url + "/rest/v1/rules/head")
