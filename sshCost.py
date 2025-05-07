#! /bin/python
# Garland R. Joseph
# 
# Get the cost of persistent ssh connections (intended for use in NJS)
#
# ----

#!/usr/bin/env python3
import subprocess
import re

def get_ssh_processes():
    """Get all SSH processes using ps command"""
    try:
        # Get detailed process info for all ssh processes
        ps_output = subprocess.check_output(
            ['ps', '-eo', 'pid,user,pcpu,pmem,rss,vsz,cmd'],
            universal_newlines=True
        )
        
        # Filter for SSH processes
        ssh_processes = []
        for line in ps_output.splitlines():
            if 'ssh' in line.lower() and not ('grep' in line or 'ps -eo' in line):
                # Clean and parse the line
                parts = re.split(r'\s+', line.strip(), maxsplit=6)
                if len(parts) == 7:
                    ssh_processes.append({
                        'pid': parts[0],
                        'user': parts[1],
                        'cpu%': float(parts[2]),
                        'mem%': float(parts[3]),
                        'rss': int(parts[4]),  # Resident Set Size (KB)
                        'vsz': int(parts[5]),  # Virtual Memory Size (KB)
                        'cmd': parts[6]
                    })
        return ssh_processes
    except subprocess.CalledProcessError as e:
        print(f"Error running ps command: {e}")
        return []

def calculate_totals(processes):
    """Calculate total resource usage across all SSH processes"""
    totals = {
        'count': len(processes),
        'cpu%': 0.0,
        'mem%': 0.0,
        'rss_kb': 0,
        'vsz_kb': 0
    }
    
    for proc in processes:
        totals['cpu%'] += proc['cpu%']
        totals['mem%'] += proc['mem%']
        totals['rss_kb'] += proc['rss']
        totals['vsz_kb'] += proc['vsz']
    
    return totals

def format_size(kb):
    """Convert KB to human-readable format"""
    for unit in ['KB', 'MB', 'GB']:
        if kb < 1024.0:
            return f"{kb:.1f} {unit}"
        kb /= 1024.0
    return f"{kb:.1f} TB"

def main():
    print("Analyzing SSH processes...\n")
    
    # Get all SSH processes
    processes = get_ssh_processes()
    
    if not processes:
        print("No SSH processes found.")
        return
    
    # Calculate totals
    totals = calculate_totals(processes)
    
    # Print individual processes
    print(f"{'PID':>6} {'USER':<8} {'CPU%':>6} {'MEM%':>6} {'RSS':>8} {'VSZ':>8} COMMAND")
    for proc in sorted(processes, key=lambda x: x['cpu%'], reverse=True):
        print(f"{proc['pid']:>6} {proc['user']:<8} {proc['cpu%']:>6.1f} "
              f"{proc['mem%']:>6.1f} {format_size(proc['rss']):>8} "
              f"{format_size(proc['vsz']):>8} {proc['cmd']}")
    
    # Print summary
    print("\n=== SSH Process Resource Summary ===")
    print(f"Total SSH processes: {totals['count']}")
    print(f"Total CPU usage: {totals['cpu%']:.1f}%")
    print(f"Total Memory usage: {totals['mem%']:.1f}%")
    print(f"Total Resident Memory (RSS): {format_size(totals['rss_kb'])}")
    print(f"Total Virtual Memory (VSZ): {format_size(totals['vsz_kb'])}")

if __name__ == "__main__":
    main()
