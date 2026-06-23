import os
from modules.base_module import BaseModule
from core.exceptions import EmptyOutputError

class CloudEnumModule(BaseModule):
    """
    Multi-cloud asset discovery (AWS, Azure, GCP).
    """
    TOOL_NAME = "cloudenum"
    PHASE = "cloud_discovery"

    def build_command(self, target: str, container_out: str) -> list:
        # target might be example.com, extract keyword example
        keyword = target.split('.')[0]
        return [
            'python3', '/opt/cloud_enum/cloud_enum.py',
            '-k', keyword,
            '-l', container_out
        ]

    def run(self, target: str, output_dir: str, tag_manager, config: dict = None, **kwargs) -> dict:
        self.config = config or {}
        
        host_output_file = os.path.join(output_dir, 'raw', 'cloudenum.txt')
        container_output_file = self._to_container_path(host_output_file)
        os.makedirs(os.path.dirname(host_output_file), exist_ok=True)
        
        keyword = target.split('.')[0]
        
        cmd = [
            'python3', '/opt/cloud_enum/cloud_enum.py',
            '-k', keyword,
            '-l', container_output_file
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
            'requests_made': 500
        }

    def emit_tags(self, run_results: dict, tag_manager) -> None:
        if run_results.get('count', 0) > 0:
            tag_manager.add("cloud_assets_found", confidence='high', source='cloudenum')

    def estimated_requests(self) -> int:
        return 500
