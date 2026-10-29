import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import ai_classifier as ai
from triage import GROUPS, classify


class AITests(unittest.TestCase):
    def setUp(self):
        self.issue = {'number': 6, 'title': 'VLLM启动失败', 'body': 'Detailed runtime reproduction. ' * 5}
        self.fallback = classify(self.issue)
        self.value = dict(self.fallback, confidence=0.95)

    def test_valid_json_and_fence(self):
        text = json.dumps(self.value)
        self.assertEqual(ai.validate(text, GROUPS)['area'], 'inference')
        self.assertEqual(ai.validate('```json\n' + text + '\n```', GROUPS)['area'], 'inference')

    def test_reject_injection_categories_and_p0(self):
        for changes in ({'priority': 'p0'}, {'area': 'shell(rm)'}, {'confidence': True}, {'confidence': 0.2}, {'reason': ''}):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                ai.validate(json.dumps(dict(self.value, **changes)), GROUPS)

    def test_agent_ready_gate(self):
        result = ai.validate(json.dumps(dict(self.value, triage='agent-ready', risk='high')), GROUPS)
        self.assertEqual(result['triage'], 'needs-review')

    def test_cli_has_no_tools_or_shell(self):
        cmd = ai.copilot_command({'executable': 'copilot.exe'})
        self.assertIn('--available-tools=', cmd)
        self.assertIn('--disable-builtin-mcps', cmd)
        self.assertNotIn('--allow-all', cmd)
        with self.assertRaises(ValueError):
            ai.copilot_command({'executable': 'copilot.cmd'})

    def test_prompt_data_and_comment_limits(self):
        value = dict(self.issue, triage_comments=[{'body': str(i)} for i in range(10)])
        prompt = ai.prompt_for(value, GROUPS)
        data = json.loads(prompt.split('ISSUE_DATA_JSON:\n')[1])
        self.assertEqual(len(data['comments']), 6)

    def test_caches_success_and_invalidates_changed_context(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(ai, 'call_copilot', return_value=json.dumps(self.value)) as call:
            config = {'provider': 'copilot', 'executable': 'copilot.exe'}
            first = ai.assess(self.issue, self.fallback, GROUPS, Path(tmp), config)
            second = ai.assess(self.issue, self.fallback, GROUPS, Path(tmp), config)
            self.assertFalse(first['cached'])
            self.assertTrue(second['cached'])
            self.assertEqual(call.call_count, 1)
            ai.assess(dict(self.issue, body='Changed'), self.fallback, GROUPS, Path(tmp), config)
            self.assertEqual(call.call_count, 2)

    def test_timeout_falls_back_without_caching_failure(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(ai, 'call_copilot', side_effect=TimeoutError):
            result = ai.assess(self.issue, self.fallback, GROUPS, Path(tmp), {'provider': 'copilot'})
            self.assertEqual(result['source'], 'rules-fallback')
            self.assertEqual(result['priority'], self.fallback['priority'])
            self.assertFalse((Path(tmp) / 'state' / 'ai-cache').exists())

    def test_low_confidence_is_cached_for_review_but_does_not_set_labels(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(ai, 'call_copilot', return_value=json.dumps(dict(self.value, confidence=0.8, priority='p3'))) as call:
            config = {'provider': 'copilot', 'executable': 'copilot.exe'}
            first = ai.assess(self.issue, self.fallback, GROUPS, Path(tmp), config)
            second = ai.assess(self.issue, self.fallback, GROUPS, Path(tmp), config)
            self.assertEqual(first['source'], 'rules-fallback')
            self.assertEqual(first['priority'], 'p1')
            self.assertEqual(first['ai_suggestion']['priority'], 'p3')
            self.assertTrue(second['cached'])
            self.assertEqual(call.call_count, 1)

    def test_no_shell_and_no_credential_copy(self):
        with tempfile.TemporaryDirectory() as tmp, patch('subprocess.run') as run:
            run.return_value.returncode = 0
            run.return_value.stdout = '{}'
            with patch.dict('os.environ', {'GH_TOKEN': 'test-only', 'COPILOT_ALLOW_ALL': 'true'}):
                ai.call_copilot('Untrusted $(payload)', {'executable': 'copilot.exe'}, Path(tmp))
            kwargs = run.call_args.kwargs
            self.assertEqual(kwargs['input'], 'Untrusted $(payload)')
            self.assertNotIn('GH_TOKEN', kwargs['env'])
            self.assertEqual(kwargs['env']['COPILOT_ALLOW_ALL'], 'false')
            self.assertFalse(kwargs.get('shell', False))

    def test_gemini_missing_key_falls_back(self):
        with tempfile.TemporaryDirectory() as tmp, patch.dict('os.environ', {}, clear=True):
            result = ai.assess(self.issue, self.fallback, GROUPS, Path(tmp), {'provider': 'gemini', 'model': 'configured-model'})
            self.assertEqual(result['source'], 'rules-fallback')


if __name__ == '__main__':
    unittest.main()
