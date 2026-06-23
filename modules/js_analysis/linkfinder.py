import os
from modules.base_module import BaseModule
from core.exceptions import EmptyOutputError

class LinkFinderModule(BaseModule):
    """
    Extracts endpoints and URLs from JavaScript files.
    """
    TOOL_NAME = "linkfinder"
    PHASE = "js_analysis"

    def build_command(self, target: str, container_out: str) -> list:
        # Expected input target is a JS file URL
        return [
            'python3', '/opt/LinkFinder/linkfinder.py',
            '-i', target,
            '-o', 'cli'
        ]

    def run(self, target: str, output_dir: str, tag_manager, config: dict = None, **kwargs) -> dict:
        self.config = config or {}
        
        # Linkfinder operates on a per-URL basis, we would typically map this across JS URLs
        # found in previous phases. For now, assume target is a file with URLs if force_domain_only is false
        
        host_output_file = os.path.join(output_dir, 'raw', 'linkfinder.txt')
        container_output_file = self._to_container_path(host_output_file)
        os.makedirs(os.path.dirname(host_output_file), exist_ok=True)
        
        host_input_file = kwargs.get('js_urls_txt')
        if not host_input_file or not os.path.exists(host_input_file):
            # If no JS URLs found, nothing to do
            return {'results': [], 'count': 0, 'requests_made': 0}

        container_input_file = self._to_container_path(host_input_file)
        
        # Using a wrapper script or bash loop inside container is common for tool taking single input
        # We will use xargs or similar inside container, but base_module handles string arrays
        # We'll just run it with a custom command if needed, but for simplicity let's assume
        # a wrapper script or direct file input if tool supports it. LinkFinder supports file input for -i
        
        cmd = [
            'python3', '/opt/LinkFinder/linkfinder.py',
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
            'requests_made': len(results) # rough estimate
        }

    def emit_tags(self, run_results: dict, tag_manager) -> None:
        if run_results.get('count', 0) > 0:
            tag_manager.add("js_endpoints_found", confidence='high', source='linkfinder')
            tag_manager.add("api_routes_in_js", confidence='medium', source='linkfinder')

    def estimated_requests(self) -> int:
        return 10
