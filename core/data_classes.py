import json
import threading
from pathlib import Path


class Module:
    def __init__(
        self,
        name,
        description,
        command,
        requirements=[],
        protocol_list=[],
        switches=[],
        analyse_func=None,
        config=None,
    ):
        """
        Represents an attack module with execution details.

        :param name: Name of the module.
        :param description: Description of the module.
        :param command: The command function or external command string.
        :param protocol_list: List of supported protocols.
        :param switches: List of command-line switches for external commands.
        :param analyse_func: Optional function for post-processing output.
        :param config: Configuration object.
        """
        self.name = name.replace(" ", "_")
        self.description = description
        self.command = command
        self.requirements = requirements or []
        self.protocol_list = protocol_list
        self.output_file = (
            str(Path(config.path) / f"{self.name}.txt") if config else None
        )
        self.switches = switches
        self.analyse_func = analyse_func

    def needs_port(self):
        return "port" in self.requirements

    def meets_requirements(self, port_data):
        # check if port is needed for module
        if "port" in self.requirements:
            if not port_data:
                return False

        # check protocols
        if self.protocol_list:
            if port_data.protocol not in self.protocol_list:
                return False

        return True

    def __str__(self):
        return f"{self.name} {self.command} {self.switches} {self.analyse_func} {self.output_file}"


class PortData:
    def __init__(
        self,
        protocol="",
        version="",
        product="",
        hostnames=None,
        modules=None,
        infos=None,
    ):
        self.protocol = protocol
        self.version = version
        self.product = product
        self.hostnames = hostnames or []
        self.modules = modules or []
        self.infos = infos or {}

    def update(self, data):
        """Merge another PortData dictionary into this instance."""
        self.protocol = self.protocol or data.get("protocol", "")
        self.version = self.version or data.get("version", "")
        self.product = self.product or data.get("product", "")
        self.hostnames.extend(
            h for h in data.get("hostnames", []) if h not in self.hostnames
        )
        self.modules.extend(m for m in data.get("modules", []) if m not in self.modules)
        self.infos.update(data.get("infos", {}))

    def to_dict(self):
        return {
            "protocol": self.protocol,
            "version": self.version,
            "product": self.product,
            "hostnames": self.hostnames,
            "modules": self.modules,
            "infos": self.infos,
        }

    @classmethod
    def from_dict(cls, data):
        return cls(
            protocol=data.get("protocol", ""),
            version=data.get("version", ""),
            product=data.get("product", ""),
            hostnames=data.get("hostnames", []),
            modules=data.get("modules", []),
            infos=data.get("infos", {}),
        )


class TargetInfo:
    def __init__(self, config, ip, hostname="", ports=None):
        self.config = config
        self.ip = ip
        self.hostname = hostname
        self.finished_modules = set()
        self.ports = {int(k): PortData.from_dict(v) for k, v in (ports or {}).items()}
        self.lock = threading.Lock()

    def add_hostname(self, port, hostname, protocol):
        with self.lock:
            if (
                port in self.ports
                and (hostname, protocol) not in self.ports[port].hostnames
            ):
                self.ports[port].hostnames.append((hostname, protocol))

    def add_information(self, port, column, info):
        with self.lock:
            if port in self.ports:
                port_data = self.ports[port]
                attr = getattr(port_data, column, None)
                if isinstance(attr, dict) and isinstance(info, dict):
                    attr.update(info)
                elif isinstance(attr, list) and isinstance(info, list):
                    attr.extend(info)
                else:
                    setattr(port_data, column, info)

    def mark_module_as_run(self, port, module_name):
        with self.lock:
            if port in self.ports:
                self.ports[port].modules.append(module_name)

            if not port:
                self.finished_modules.add(module_name)

    def check_module_finished(self, port, module_name):
        with self.lock:
            return port in self.ports and module_name in self.ports[port].modules

    def get_ports_dict_data(self):
        with self.lock:
            return {port: data.to_dict() for port, data in self.ports.items()}

    def get_port(self, port):
        with self.lock:
            if port in self.ports:
                return self.ports[port]
            else:
                return None

    def get_host(self):
        return self.hostname if self.hostname else self.ip

    def merge(self, other_ports):
        with self.lock:
            if other_ports:
                for port, data in other_ports.items():
                    if port not in self.ports:
                        self.ports[port] = PortData.from_dict(data)
                    else:
                        self.ports[port].update(data)

    def to_dict(self):
        return {
            "ip": self.ip,
            "hostname": self.hostname,
            "ports": {port: data.to_dict() for port, data in self.ports.items()},
        }

    @classmethod
    def from_dict(cls, config, dict):
        return cls(
            config=config, ip=dict["ip"], hostname=dict["hostname"], ports=dict["ports"]
        )

    def save_to_file(self):
        with self.lock:
            try:
                save_path = Path(self.config.path) / "pyae_save.json"
                with open(save_path, "w") as file:
                    json.dump(self.to_dict(), file)
            except Exception as e:
                self.config.log_error(f"Exception in save_data: {e}")
