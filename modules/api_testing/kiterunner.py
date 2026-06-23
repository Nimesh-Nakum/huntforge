import os
from modules.base_module import BaseModule
from core.exceptions import EmptyOutputError

class KiterunnerModule(BaseModule):
    """
    API endpoint discovery using real-world route wordlists.
    """
    TOOL_NAME = "kiterunner"
    PHASE = "api_testing"

    def build_command(self, target: str, container_out: str) -> list:
        # Default fallback if single target
        wordlist = self._cfg('wordlist', '/opt/wordlists/routes-large.json')
        return [
            'kr', 'brute', target,
            '-w', wordlist,
            '-o', 'json',
            '-x', '5',
            '--fail-status-codes', '404,502'
        ]

    def run(self, target: str, output_dir: str, tag_manager, config: dict = None, **kwargs) -> dict:
        self.config = config or {}
        
        host_output_file = os.path.join(output_dir, 'raw', 'kiterunner.json')
        container_output_file = self._to_container_path(host_output_file)
        os.makedirs(os.path.dirname(host_output_file), exist_ok=True)
        
        host_input_file = kwargs.get('live_hosts_txt')
        if not host_input_file or not os.path.exists(host_input_file):
            return {'results': [], 'count': 0, 'requests_made': 0}

        container_input_file = self._to_container_path(host_input_file)
        wordlist = self._cfg('wordlist', '/opt/wordlists/routes-large.json')
        
        cmd = [
            'kr', 'brute', container_input_file,
            '-w', wordlist,
            '-o', 'json',
            '-x', '5',
            '--fail-status-codes', '404,502'
        ]
        
        # Note: kiterunner stdout is json but not to a file natively with -o json in some versions
        # Assume it can redirect or writes to stdout
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
            'requests_made': len(results) * 100 # rough estimate
        }

    def emit_tags(self, run_results: dict, tag_manager) -> None:
        if run_results.get('count', 0) > 0:
            tag_manager.add("api_endpoints_found", confidence='high', source='kiterunner')
            tag_manager.add("hidden_api_routes", confidence='medium', source='kiterunner')

    def estimated_requests(self) -> int:
        return 5000
