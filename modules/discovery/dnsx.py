import os
from modules.base_module import BaseModule
from core.exceptions import EmptyOutputError
import json

class DnsxModule(BaseModule):
    """
    DNS resolution and wildcard detection.
    """
    TOOL_NAME = "dnsx"
    PHASE = "discovery"

    def build_command(self, target: str, container_out: str) -> list:
        return [
            'dnsx', '-d', target,
            '-json', '-o', container_out,
            '-a', '-aaaa', '-cname', '-mx', '-resp', '-silent'
        ]

    def run(self, target: str, output_dir: str, tag_manager, config: dict = None, **kwargs) -> dict:
        self.config = config or {}
        
        host_output_file = os.path.join(output_dir, 'raw', 'dnsx.json')
        container_output_file = self._to_container_path(host_output_file)
        os.makedirs(os.path.dirname(host_output_file), exist_ok=True)
        
        host_input_file = kwargs.get('subdomains_txt')
        if not host_input_file or not os.path.exists(host_input_file):
            return {'results': [], 'count': 0, 'requests_made': 0}

        container_input_file = self._to_container_path(host_input_file)
        
        cmd = [
            'dnsx', '-l', container_input_file,
            '-json', '-o', container_output_file,
            '-a', '-aaaa', '-cname', '-mx', '-resp', '-silent'
        ]
        
        self._run_subprocess(cmd, host_output_file)
        
        results = []
        try:
            content = self._read_output_file(host_output_file)
            for line in content.splitlines():
                if line.strip():
                    results.append(json.loads(line))
        except (EmptyOutputError, json.JSONDecodeError):
            pass
            
        return {
            'results': results,
            'count': len(results),
            'requests_made': len(results)
        }

    def emit_tags(self, run_results: dict, tag_manager) -> None:
        if run_results.get('count', 0) > 0:
            tag_manager.add_tag("cname_records_found", confidence=100)
            tag_manager.add_tag("dns_resolved", confidence=100)

    def estimated_requests(self) -> int:
        return 1000
