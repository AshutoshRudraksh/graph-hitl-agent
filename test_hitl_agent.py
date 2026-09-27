import unittest

from langgraph.types import Command

from hitl_agent import build_graph


class HitlAgentTests(unittest.TestCase):
    def setUp(self) -> None:
        self.graph = build_graph()

    def test_direct_answer_without_tool(self):
        result = self.graph.invoke(
            {"user_message": "Hello there"},
            config={"configurable": {"thread_id": "direct"}},
        )
        self.assertIn("response", result)
        self.assertNotIn("lookup_result", result)
        self.assertNotIn("transfer_result", result)

    def test_safe_account_lookup_runs_without_approval(self):
        result = self.graph.invoke(
            {"user_message": "What is the balance for account 1234?"},
            config={"configurable": {"thread_id": "lookup"}},
        )
        self.assertEqual(result["lookup_result"]["account_id"], "1234")
        self.assertIn("balance", result["lookup_result"])

    def test_transfer_requires_human_approval_then_resumes(self):
        config = {"configurable": {"thread_id": "transfer-approve"}}
        first_step = self.graph.invoke({"user_message": "Transfer $50 to savings"}, config=config)
        self.assertIn("__interrupt__", first_step)

        resumed = self.graph.invoke(Command(resume="approve"), config=config)
        self.assertEqual(resumed["transfer_result"]["status"], "completed")
        self.assertEqual(resumed["approval"], "approved")
        self.assertEqual(resumed["transfer_result"]["source_account"], "1234")
        self.assertEqual(resumed["transfer_result"]["destination_account"], "5678")

    def test_transfer_rejection_is_persisted_and_stops_execution(self):
        config = {"configurable": {"thread_id": "transfer-reject"}}
        first_step = self.graph.invoke({"user_message": "Send 25 to account 5678"}, config=config)
        self.assertIn("__interrupt__", first_step)

        resumed = self.graph.invoke(Command(resume="reject"), config=config)
        self.assertEqual(resumed["approval"], "rejected")
        self.assertEqual(resumed["transfer_result"]["status"], "rejected")


if __name__ == "__main__":
    unittest.main()
