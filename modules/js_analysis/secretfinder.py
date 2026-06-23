import os
from modules.base_module import BaseModule
from core.exceptions import EmptyOutputError

class SecretFinderModule(BaseModule):
    """
    Extracts API keys and secrets from JavaScript files.
    """
    TOOL_NAME = "secretfinder"
    PHASE = "js_analysis"

    def build_command(self, target: str, container_out: str) -> list:
        return [
            'python3', '/opt/SecretFinder/SecretFinder.py',
            '-i', target,
            '-o', 'cli'
        ]

    def run(self, target: str, output_dir: str, tag_manager, config: dict = None, **kwargs) -> dict:
        self.config = config or {}
        
        host_output_file = os.path.join(output_dir, 'raw', 'secretfinder.txt')
        container_output_file = self._to_container_path(host_output_file)
        os.makedirs(os.path.dirname(host_output_file), exist_ok=True)
        
        host_input_file = kwargs.get('js_urls_txt')
        if not host_input_file or not os.path.exists(host_input_file):
            return {'results': [], 'count': 0, 'requests_made': 0}

        container_input_file = self._to_container_path(host_input_file)
        
        cmd = [
            'python3', '/opt/SecretFinder/SecretFinder.py',
            '-i', container_input_file,
            '-o', 'cli'
        ]
        
        self._run_subprocess(cmd, host_output_file)
        
        results = []
        try:
            content = self._read_output_file(host_output_file)
            for line in content.splitlines():
                if line.strip():
                    results.append(line.strip())
        except EmptyOutputError:
            pass
            
        return {
            'results': results,
            'count': len(results),
            'requests_made': 10
        }

    def emit_tags(self, run_results: dict, tag_manager) -> None:
        if run_results.get('count', 0) > 0:
            tag_manager.add("js_secrets_found", confidence='high', source='secretfinder')
            tag_manager.add("api_keys_in_js", confidence='medium', source='secretfinder')

    def estimated_requests(self) -> int:
        return 10
