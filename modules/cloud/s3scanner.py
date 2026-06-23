import os
from modules.base_module import BaseModule
from core.exceptions import EmptyOutputError

class S3ScannerModule(BaseModule):
    """
    Amazon S3 bucket enumeration.
    """
    TOOL_NAME = "s3scanner"
    PHASE = "cloud_discovery"

    def build_command(self, target: str, container_out: str) -> list:
        # Assuming target is a bucket name or domain
        return [
            's3scanner', 'scan',
            '--bucket', target
        ]

    def run(self, target: str, output_dir: str, tag_manager, config: dict = None, **kwargs) -> dict:
        self.config = config or {}
        
        host_output_file = os.path.join(output_dir, 'raw', 's3scanner.txt')
        container_output_file = self._to_container_path(host_output_file)
        os.makedirs(os.path.dirname(host_output_file), exist_ok=True)
        
        cmd = [
            's3scanner', 'scan',
            '--bucket', target
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
            tag_manager.add("s3_buckets_found", confidence='high', source='s3scanner')

    def estimated_requests(self) -> int:
        return 50
