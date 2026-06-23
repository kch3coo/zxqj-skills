from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path


MODULE_PATH = (
    Path(__file__).resolve().parents[1] / "scripts" / "devflow_manage_tasks.py"
)


def load_module():
    spec = importlib.util.spec_from_file_location("devflow_manage_tasks", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class DevflowManageTasksTest(unittest.TestCase):
    def test_parse_plain_text_blocks_uses_first_line_as_title(self):
        mod = load_module()
        text = """数据结构与基础对象调整
补充销售订单、销售发货单、虚拟锁仓所需基础字段和记录能力。

销售订单审批与销售发货单生成联动整理
保留销售发货单自动生成逻辑。销售订单无需审批或审批通过后继续生成销售发货单。
"""

        tasks = mod.parse_plain_text_tasks(text)

        self.assertEqual(
            [task.title for task in tasks],
            ["数据结构与基础对象调整", "销售订单审批与销售发货单生成联动整理"],
        )
        self.assertEqual(tasks[0].body, "补充销售订单、销售发货单、虚拟锁仓所需基础字段和记录能力。")

    def test_match_req_range_limits_to_story_and_number_range(self):
        mod = load_module()
        tasks = [
            {"id": 670, "storyId": 112, "title": "REQ-01 数据库模型与字段扩展"},
            {"id": 682, "storyId": 112, "title": "REQ-13 并发一致性与幂等控制"},
            {"id": 683, "storyId": 112, "title": "REQ-14 不应删除"},
            {"id": 700, "storyId": 999, "title": "REQ-01 其他 Story 不应删除"},
            {"id": 701, "storyId": 112, "title": "普通任务不应删除"},
        ]

        matched = mod.match_req_tasks(tasks, story_id=112, first=1, last=13)

        self.assertEqual([task["id"] for task in matched], [670, 682])

    def test_build_dry_run_plan_does_not_call_write_methods(self):
        mod = load_module()
        client = RecordingClient()
        task_specs = [
            mod.TaskInput(title="新任务", body="任务描述"),
        ]

        plan = mod.build_replacement_plan(
            client=client,
            project_id=2,
            sprint_id=7,
            story_id=112,
            story_title="销售&库存&每日生产计划联动",
            delete_first=1,
            delete_last=13,
            task_specs=task_specs,
            workflow_template_name="软件开发流程",
            developer_nickname="陈一安",
            tester_nickname="颜沛杰",
            start_time="2026-05-07 00:00:00",
            due_time="2026-05-11 23:59:59",
        )

        self.assertEqual(client.write_calls, [])
        self.assertEqual([task["id"] for task in plan.delete_tasks], [670, 671])
        self.assertEqual(plan.create_tasks[0].payload["assigneeUserId"], 145)
        self.assertEqual(plan.create_tasks[0].workflow_payload["nodeUpdates"][0]["assigneeUserId"], 145)
        self.assertEqual(plan.create_tasks[0].workflow_payload["nodeUpdates"][1]["assigneeUserId"], 144)


class RecordingClient:
    write_calls: list[str]

    def __init__(self):
        self.write_calls = []

    def get_story_page(self, project_id: int, sprint_id: int):
        return [
            {
                "id": 112,
                "title": "销售&库存&每日生产计划联动",
                "projectId": project_id,
                "sprintId": sprint_id,
            }
        ]

    def get_task_page(self, project_id: int, sprint_id: int):
        return [
            {"id": 670, "storyId": 112, "title": "REQ-01 数据库模型与字段扩展"},
            {"id": 671, "storyId": 112, "title": "REQ-02 ATP 可用库存与库存占用服务"},
            {"id": 700, "storyId": 999, "title": "REQ-01 其他 Story 不应删除"},
        ]

    def get_workflow_template(self, project_id: int, name: str):
        return {
            "id": 1,
            "name": name,
            "nodes": [
                {"id": 1, "nodeName": "开发", "seqNo": 1},
                {"id": 2, "nodeName": "测试", "seqNo": 2},
            ],
        }

    def get_users(self):
        return [
            {"id": 145, "nickname": "陈一安"},
            {"id": 144, "nickname": "颜沛杰"},
        ]

    def create_task(self, payload):
        self.write_calls.append("create_task")

    def delete_task(self, task_id):
        self.write_calls.append("delete_task")

    def update_workflow(self, payload):
        self.write_calls.append("update_workflow")


if __name__ == "__main__":
    unittest.main()
