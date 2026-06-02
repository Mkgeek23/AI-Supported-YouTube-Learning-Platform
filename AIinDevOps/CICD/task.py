import subprocess
import os


class CICDBuilder:
    def __init__(self, script_path="local-ci-cd.sh"):
        self.script_path = script_path

    def build(self):
        """Execute the local-ci-cd.sh script"""
        try:
            # Make sure the script is executable
            os.chmod(self.script_path, 0o755)

            # Run the script
            result = subprocess.run(
                [f"./{self.script_path}"],
                check=True,
                capture_output=True,
                text=True,
                shell=True
            )
            return True, result.stdout
        except subprocess.CalledProcessError as e:
            return False, e.stderr


if __name__ == '__main__':
    builder = CICDBuilder()
    success, output = builder.build()
