"""Attack thread implementation for PyAutoEnum using modern threading patterns."""

import concurrent.futures
import queue
import subprocess
import threading
import time
import traceback
from dataclasses import dataclass
from enum import Enum, auto
from typing import Any, Callable, Dict, List, Optional, Union

from pyautoenum.config.manager import ConfigManager


class TaskStatus(Enum):
    """Status of a task execution."""
    PENDING = auto()
    RUNNING = auto()
    COMPLETED = auto()
    FAILED = auto()


@dataclass
class AttackTask:
    """Represents a task to be executed by the thread pool."""
    module: Any
    port: Optional[Union[str, int]] = None
    status: TaskStatus = TaskStatus.PENDING
    progress: float = 0.0
    start_time: float = 0.0
    end_time: float = 0.0
    output: str = ""
    error: str = ""
    

class AttackThreadPool:
    """Thread pool for running attack modules against targets."""
    
    def __init__(self, max_workers: Optional[int] = None):
        """
        Initialize the attack thread pool.
        
        Args:
            max_workers: Maximum number of worker threads, defaults to (CPU count + 4)
        """
        # Use a slightly higher number of threads than CPU cores for I/O bound tasks
        self.max_workers = max_workers or (threading.active_count() + 4)
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers)
        self.task_queue = queue.Queue()
        self.tasks: Dict[str, AttackTask] = {}
        self.running = False
        self.worker_thread = threading.Thread(target=self._process_queue, daemon=True)
        self.lock = threading.RLock()
        self._stop_event = threading.Event()
        
        # Statistics tracking
        self.stats = {
            "pending": 0,
            "running": 0,
            "completed": 0,
            "failed": 0,
            "total": 0
        }
    
    def start(self):
        """Start processing the task queue."""
        # 
        with self.lock:
            if not self.running:
                # 
                self.running = True
                self._stop_event.clear()
                try:
                    # 
                    self.worker_thread = threading.Thread(target=self._process_queue, daemon=True)
                    self.worker_thread.start()
                    
                    ConfigManager.log_info(f"Attack thread pool started with {self.max_workers} workers")
                except Exception as e:
                    
                    
                    ConfigManager.log_error(f"Error starting worker thread: {str(e)}")
            else:
                # 
                pass
    
    def stop(self):
        """Stop processing the task queue."""
        # 
        with self.lock:
            # 
            self._stop_event.set()
            self.running = False
            # 
            ConfigManager.log_info("Attack thread pool stopping...")
    
    def add_task(self, module: Any, port: Optional[Union[str, int]] = None) -> str:
        """
        Add a task to the queue.
        
        Args:
            module: Module to run
            port: Target port or None for target-wide modules
            
        Returns:
            Task ID
        """
        task_id = f"{module.name}_{port if port else 'target'}"
        
        with self.lock:
            # Check if task is already in queue
            if task_id in self.tasks:
                return task_id
                
            # Create new task
            task = AttackTask(module=module, port=port)
            self.tasks[task_id] = task
            self.task_queue.put(task_id)
            
            # Update stats
            self.stats["pending"] += 1
            self.stats["total"] += 1
            
            ConfigManager.log_info(f"Added task to queue: {module.name} for {'port ' + str(port) if port else 'target'}")
            
        return task_id
    
    def get_task_status(self, task_id: str) -> Optional[TaskStatus]:
        """
        Get the status of a task.
        
        Args:
            task_id: ID of the task
            
        Returns:
            Task status or None if task not found
        """
        with self.lock:
            task = self.tasks.get(task_id)
            if task:
                return task.status
        return None
    
    def get_stats(self) -> Dict[str, int]:
        """
        Get current statistics of the thread pool.
        
        Returns:
            Dictionary with current task statistics
        """
        with self.lock:
            return self.stats.copy()
    
    def _process_queue(self):
        """Process tasks from the queue until stopped."""
        
        while not self._stop_event.is_set():
            try:
                # Get a task from the queue with a timeout
                try:
                    # 
                    task_id = self.task_queue.get(timeout=1.0)
                    
                except queue.Empty:
                    continue
                
                # Get the task
                with self.lock:
                    task = self.tasks.get(task_id)
                    if not task:
                        
                        self.task_queue.task_done()
                        continue
                    
                    # Update task status
                    
                    task.status = TaskStatus.RUNNING
                    task.start_time = time.time()
                    self.stats["pending"] -= 1
                    self.stats["running"] += 1
                
                # Submit task to thread pool
                future = self.executor.submit(self._execute_task, task_id)
                
                # Register callback for task completion
                future.add_done_callback(lambda f, tid=task_id: self._task_done(tid, f))
                
            except Exception:
                ConfigManager.log_error(
                    f"Exception in thread pool worker: {traceback.format_exc()}"
                )
    
    def _execute_task(self, task_id: str) -> bool:
        """
        Execute a task.
        
        Args:
            task_id: ID of the task
            
        Returns:
            Success status
        """
        with self.lock:
            task = self.tasks.get(task_id)
            if not task:
                return False
                
        try:
            ConfigManager.log_info(f"Started Module: {task.module.name}")
            
            # Ensure target_info is available before proceeding
            if not ConfigManager.target_info:
                task.error = "No target information available"
                ConfigManager.log_error(task.error)
                return False
            
            # Mark module as completed in TargetInfo
            ConfigManager.target_info.mark_module_as_run(task.port, task.module.name)
            
            # Check if the command is a Python function
            func = self._get_callable_func(task.module.command)
            if func:
                # Run Python function
                task.output = func(ConfigManager.target_info, task.port, task.module.switches)
            else:
                # Run external command
                task.output = self._run_external_command(task)
            
            ConfigManager.log_success(f"Finished Module: {task.module.name}")
            
            # Run analysis if needed
            if task.module.analyse_func:
                self._process_analysis(task)
                
            return True
            
        except Exception as e:
            task.error = f"Exception in AttackTask ({task.module.name}): {str(e)}\n{traceback.format_exc()}"
            ConfigManager.log_error(task.error)
            return False
    
    def _task_done(self, task_id: str, future) -> None:
        """
        Handle task completion.
        
        Args:
            task_id: ID of the task
            future: Future object from the executor
        """
        with self.lock:
            task = self.tasks.get(task_id)
            if not task:
                return
                
            task.end_time = time.time()
            self.stats["running"] -= 1
            
            # Update task status based on success/failure
            try:
                success = future.result()
                if success:
                    task.status = TaskStatus.COMPLETED
                    task.progress = 100.0
                    self.stats["completed"] += 1
                else:
                    task.status = TaskStatus.FAILED
                    self.stats["failed"] += 1
            except Exception:
                task.status = TaskStatus.FAILED
                task.error += f"\nException during task completion: {traceback.format_exc()}"
                self.stats["failed"] += 1
            
            # Save target info after each task completes
            if ConfigManager.target_info:
                ConfigManager.target_info.save_to_file()
                
            self.task_queue.task_done()
    
    def _get_callable_func(self, cmd: str) -> Optional[Callable]:
        """
        Get a callable function from module name.
        
        Args:
            cmd: Function name
            
        Returns:
            Callable function or None
        """
        # Try to find function in modules.custom
        from pyautoenum.modules import custom
        if hasattr(custom, cmd) and callable(getattr(custom, cmd)):
            return getattr(custom, cmd)
            
        return None
    
    def _run_external_command(self, task: AttackTask) -> str:
        """Run an external command and capture output to a file."""
        try:
            # Format command with arguments
            cmd = [task.module.command] + self._format_switches(task)
            cmd_str = " ".join(cmd)
            ConfigManager.log_info(f"Running command: {cmd_str}")
            
            # Execute command with progress monitoring
            process = subprocess.Popen(
                cmd, 
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            
            output = []
            # Poll the process and update progress
            if process.stdout:
                while True:
                    line = process.stdout.readline()
                    if not line and process.poll() is not None:
                        break
                    if line:
                        output.append(line)
                        with self.lock:
                            # Update progress based on output lines as a rough estimate
                            task.progress = min(99.0, task.progress + 0.5)
            
            process.wait()
            
            # Write output to file
            with open(task.module.output_file, "w") as outfile:
                outfile.write("".join(output))
            
            return "".join(output)
                
        except Exception as e:
            error_msg = f"Error running command {task.module.command}: {str(e)}"
            ConfigManager.log_error(error_msg)
            return error_msg
    
    def _format_switches(self, task: AttackTask) -> List[str]:
        """
        Format command-line switches with target-specific values.
        
        Args:
            task: The task containing the module and port
            
        Returns:
            List of formatted command-line switches
        """
        if not ConfigManager.target_info:
            return []
            
        port_data = ConfigManager.target_info.get_port(task.port)
        hostname = ConfigManager.target_info.get_host()
        
        return [
            switch.replace(
                "[protocol]",
                port_data.protocol if port_data else f"port_{task.port}_no_data",
            )
            .replace("[hostname]", hostname)
            .replace("[port]", str(task.port) if task.port else "")
            .replace("[outfile]", task.module.output_file)
            for switch in task.module.switches
        ]
    
    def _process_analysis(self, task: AttackTask) -> None:
        """Handle analysis of the output after execution."""
        analyse_func = self._get_callable_func(task.module.analyse_func)
        if analyse_func:
            try:
                if not ConfigManager.target_info:
                    task.error = "No target information available for analysis"
                    ConfigManager.log_error(task.error)
                    return
                    
                analyse_func(ConfigManager.target_info, task.output)
                ConfigManager.log_info(f"Analysis completed for {task.module.name}")
            except Exception as e:
                error_msg = f"Error in analysis for {task.module.name}: {str(e)}"
                task.error = error_msg
                ConfigManager.log_error(error_msg)
        else:
            ConfigManager.log_warning(f"Analysis function {task.module.analyse_func} not found for {task.module.name}")


# Create a global thread pool instance
attack_thread_pool = AttackThreadPool()
