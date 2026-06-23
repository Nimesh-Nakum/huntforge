import os
from modules.base_module import BaseModule
from core.exceptions import EmptyOutputError
import json

class RetireJsModule(BaseModule):
    """
    Detects known-vulnerable JavaScript libraries using Retire.js
    """
    TOOL_NAME = "retirejs"
    PHASE = "js_analysis"

    def build_command(self, target: str, container_out: str) -> list:
        return [
            'retire', '--js',
            '--outputformat', 'json',
            '--outputpath', container_out
        ]

    def run(self, target: str, output_dir: str, tag_manager, config: dict = None, **kwargs) -> dict:
        self.config = config or {}
        
        host_output_file = os.path.join(output_dir, 'raw', 'retirejs.json')
        container_output_file = self._to_container_path(host_output_file)
        os.makedirs(os.path.dirname(host_output_file), exist_ok=True)
        
        # Retire.js usually runs against a directory or can be fed URLs.
        # We will assume it's running against downloaded JS files or a target URL directory.
        # For simplicity, we just run it against the target domain if it supports remote scanning,
        # or against downloaded files. Let's use the js_urls_txt if available.
        
        host_input_file = kwargs.get('js_urls_txt')
        if host_input_file and os.path.exists(host_input_file):
            container_input_file = self._to_container_path(host_input_file)
            cmd = [
                'retire', '--js', '--jspath', container_input_file,
                '--outputformat', 'json',
                '--outputpath', container_output_file
            ]
        else:
            # Fallback to direct URL scan if supported or skip
            return {'results': [], 'count': 0, 'requests_made': 0}
        
        self._run_subprocess(cmd, host_output_file)
        
        results = []
        try:
            content = self._read_output_file(host_output_file)
            data = json.loads(content)
            results = data.get('data', [])
        except (EmptyOutputError, json.JSONDecodeError):
            pass
            
        return {
            'results': results,
            'count': len(results),
            'requests_made': len(results)
        }

    def emit_tags(self, run_results: dict, tag_manager) -> None:
        if run_results.get('count', 0) > 0:
            tag_manager.add_tag("vulnerable_js_libs", confidence=100)
            tag_manager.add_tag("outdated_js", confidence=90)

    def estimated_requests(self) -> int:
        return 5
