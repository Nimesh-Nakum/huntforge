import os
from modules.base_module import BaseModule
from core.exceptions import EmptyOutputError

class JwtToolModule(BaseModule):
    """
    JWT token analysis module.
    """
    TOOL_NAME = "jwt_tool"
    PHASE = "api_testing"

    def build_command(self, target: str, container_out: str) -> list:
        return [
            'python3', '/opt/jwt_tool/jwt_tool.py',
            '-t', target,
            '-M', 'at'
        ]

    def run(self, target: str, output_dir: str, tag_manager, config: dict = None, **kwargs) -> dict:
        self.config = config or {}
        
        host_output_file = os.path.join(output_dir, 'raw', 'jwt_tool.txt')
        container_output_file = self._to_container_path(host_output_file)
        os.makedirs(os.path.dirname(host_output_file), exist_ok=True)
        
        # Needs JWT tokens extracted from previous phases to test.
        # Assume tags or kwargs provide it
        jwt_tokens_file = kwargs.get('jwt_tokens_txt')
        if not jwt_tokens_file or not os.path.exists(jwt_tokens_file):
            return {'results': [], 'count': 0, 'requests_made': 0}
            
        container_input_file = self._to_container_path(jwt_tokens_file)

        cmd = [
            'python3', '/opt/jwt_tool/jwt_tool.py',
            '-I', container_input_file,
            '-M', 'at'
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
            'requests_made': 50
        }

    def emit_tags(self, run_results: dict, tag_manager) -> None:
        if run_results.get('count', 0) > 0:
            tag_manager.add("jwt_vuln_found", confidence='high', source='jwt_tool')
            tag_manager.add("jwt_weak_secret", confidence='medium', source='jwt_tool')

    def estimated_requests(self) -> int:
        return 100
