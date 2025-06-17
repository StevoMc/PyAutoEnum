"""Data model definitions for PyAutoEnum."""

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Union


class Module:
    """
    Represents an attack module with execution details.
    """

    def __init__(
        self,
        name: str,
        description: str,
        command: str,
        requirements: List[str] = list(),
        protocol_list: List[str] = list(),
        switches: List[str] = list(),
        analyse_func: str = str(),
        config=None,
    ):
        """
        Initialize a module with its parameters and requirements.

        Args:
            name: Name of the module
            description: Description of the module
            command: Command to execute (system command or function name)
            requirements: List of requirements (e.g., "port")
            protocol_list: List of protocols the module supports
            switches: Command-line switches for external commands
            analyse_func: Optional function name for analyzing output
            config: Configuration manager instance
        """
        self.name = name.replace(" ", "_")
        self.description = description
        self.command = command
        self.requirements = requirements or []
        self.protocol_list = protocol_list or []

        # Set output file path if config is provided
        if config and hasattr(config, "path"):
            self.output_file = str(Path(config.path) / f"{self.name}.txt")
        else:
            self.output_file = f"{self.name}.txt"

        self.switches = switches or []
        self.analyse_func = analyse_func

    def needs_port(self) -> bool:
        """Check if the module requires a port number."""
        return "port" in self.requirements

    def meets_requirements(self, port_data) -> bool:
        """
        Check if port data meets module requirements.

        Args:
            port_data: PortData instance to check against

        Returns:
            Boolean indicating if requirements are met
        """
        # Check if port is needed for module
        if "port" in self.requirements and not port_data:
            return False

        # Check protocols
        if self.protocol_list and port_data.protocol:
            if port_data.protocol not in self.protocol_list:
                return False

        return True

    def __str__(self) -> str:
        """String representation of the module."""
        return f"{self.name} {self.command} {self.switches} {self.analyse_func} {self.output_file}"


class PortData:
    """
    Stores information about a network port.
    """

    def __init__(
        self,
        protocol: str = "",
        version: str = "",
        product: str = "",
        hostnames: List[str] = list(),
        modules: List[str] = list(),
        infos: Dict[str, Any] = dict(),
    ):
        """
        Initialize port data with service information.

        Args:
            protocol: Service protocol (e.g., "http", "ssh")
            version: Service version
            product: Service product name
            hostnames: List of hostnames associated with this port
            modules: List of modules that have run against this port
            infos: Additional information about the port/service
        """
        self.protocol = protocol
        self.version = version
        self.product = product
        self.hostnames = hostnames or []
        self.modules = modules or []
        self.infos = infos or {}

    def update(self, data: Dict[str, Any]) -> None:
        """
        Update this instance with data from a dictionary.

        Args:
            data: Dictionary with port data
        """
        self.protocol = self.protocol or data.get("protocol", "")
        self.version = self.version or data.get("version", "")
        self.product = self.product or data.get("product", "")

        # Update hostnames without duplicating
        if "hostnames" in data and data["hostnames"]:
            for hostname in data["hostnames"]:
                if hostname not in self.hostnames:
                    self.hostnames.append(hostname)

        # Update modules without duplicating
        if "modules" in data and data["modules"]:
            for module in data["modules"]:
                if module not in self.modules:
                    self.modules.append(module)

        # Update infos, merging dictionaries
        if "infos" in data and data["infos"]:
            self.infos.update(data["infos"])

    def to_dict(self) -> Dict[str, Any]:
        """Convert port data to a dictionary."""
        return {
            "protocol": self.protocol,
            "version": self.version,
            "product": self.product,
            "hostnames": self.hostnames,
            "modules": self.modules,
            "infos": self.infos,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PortData":
        """
        Create a PortData instance from a dictionary.

        Args:
            data: Dictionary with port data

        Returns:
            New PortData instance
        """
        return cls(
            protocol=data.get("protocol", ""),
            version=data.get("version", ""),
            product=data.get("product", ""),
            hostnames=data.get("hostnames", []),
            modules=data.get("modules", []),
            infos=data.get("infos", {}),
        )


class TargetInfo:
    """
    Stores all information about a target system.
    """

    def __init__(
        self,
        config,
        ip: str = "",
        hostname: str = "",
        ports: Dict[str, PortData] = dict(),
    ):
        """
        Initialize target information.

        Args:
            config: Configuration manager instance
            ip: Target IP address
            hostname: Target hostname
            ports: Dictionary of port data keyed by port number
        """
        self.config = config
        self.ip = ip
        self.hostname = hostname
        self.ports = ports or {}

    def add_hostname(self, port: Union[str, int], hostname: str, protocol: str) -> None:
        """
        Add a hostname to a port.

        Args:
            port: Port number
            hostname: Hostname to add
            protocol: Protocol used (e.g., "http")
        """
        port_str = str(port)
        if port_str not in self.ports:
            self.ports[port_str] = PortData(protocol=protocol)

        if hostname not in self.ports[port_str].hostnames:
            self.ports[port_str].hostnames.append(hostname)

    def add_information(self, port: Union[str, int], column: str, info: Any) -> None:
        """
        Add additional information to a port.

        Args:
            port: Port number
            column: Information category
            info: Information to add
        """
        port_str = str(port)
        if port_str not in self.ports:
            self.ports[port_str] = PortData()

        self.ports[port_str].infos[column] = info

    def mark_module_as_run(
        self, port: Optional[Union[str, int]], module_name: str
    ) -> None:
        """
        Mark a module as having been run against a port.

        Args:
            port: Port number or None for target-wide modules
            module_name: Name of the module
        """
        if port is None:
            # Handle target-wide modules (not port-specific)
            return

        port_str = str(port)
        if port_str not in self.ports:
            self.ports[port_str] = PortData()

        if module_name not in self.ports[port_str].modules:
            self.ports[port_str].modules.append(module_name)

    def check_module_finished(self, port: Union[str, int], module_name: str) -> bool:
        """
        Check if a module has already run against a port.

        Args:
            port: Port number
            module_name: Name of the module

        Returns:
            Boolean indicating if module has run
        """
        port_str = str(port)
        if port_str not in self.ports:
            return False

        return module_name in self.ports[port_str].modules

    def get_ports_dict_data(self) -> Dict[str, Dict[str, str]]:
        """
        Get formatted port data for display.

        Returns:
            Dictionary with port data in display format
        """
        result = {}
        for port, port_data in self.ports.items():
            result[port] = {
                "protocol": port_data.protocol,
                "product": port_data.product,
                "version": port_data.version,
                "modules": ", ".join(port_data.modules),
            }
        return result

    def get_port(self, port: Optional[Union[str, int]]) -> Optional[PortData]:
        """
        Get data for a specific port.

        Args:
            port: Port number or None

        Returns:
            PortData instance or None if port doesn't exist
        """
        if port is None:
            return None

        port_str = str(port)
        return self.ports.get(port_str)

    def get_host(self) -> str:
        """
        Get the primary host identifier (hostname or IP).

        Returns:
            Hostname if available, otherwise IP address
        """
        return self.hostname if self.hostname else self.ip

    def merge(self, other_ports: Dict[str, Dict[str, Any]]) -> None:
        """
        Merge port data from another source.

        Args:
            other_ports: Dictionary of port data to merge
        """
        for port, data in other_ports.items():
            if port not in self.ports:
                self.ports[port] = PortData.from_dict(data)
            else:
                self.ports[port].update(data)

    def to_dict(self) -> Dict[str, Any]:
        """Convert target info to a dictionary."""
        return {
            "ip": self.ip,
            "hostname": self.hostname,
            "ports": {
                port: port_data.to_dict() for port, port_data in self.ports.items()
            },
        }

    @classmethod
    def from_dict(cls, config, data: Dict[str, Any]) -> "TargetInfo":
        """
        Create a TargetInfo instance from a dictionary.

        Args:
            config: Configuration manager instance
            data: Dictionary with target data

        Returns:
            New TargetInfo instance
        """
        ports = {}
        for port, port_data in data.get("ports", {}).items():
            ports[port] = PortData.from_dict(port_data)

        return cls(
            config=config,
            ip=data.get("ip", ""),
            hostname=data.get("hostname", ""),
            ports=ports,
        )

    def save_to_file(self) -> None:
        """Save target information to a JSON file."""
        if not self.config or not hasattr(self.config, "path"):
            return

        try:
            file_path = os.path.join(self.config.path, f"{self.get_host()}.json")
            with open(file_path, "w") as f:
                json.dump(self.to_dict(), f, indent=2)
        except Exception as e:
            if hasattr(self.config, "log_error"):
                self.config.log_error(f"Failed to save target info: {str(e)}")
            else:
                pass
                
