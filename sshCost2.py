#!/usr/bin/env python
import subprocess
import re

def get_ssh_processes():
    """Get all SSH processes using ps command"""
    try:
        # Get detailed process info for all ssh processes
        ps_output = subprocess.check_output(
            ['ps', '-eo', 'pid,user,pcpu,pmem,rss,vsz,cmd']
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
        print("Error running ps command: %s" % e)
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
            return "%.1f %s" % (kb, unit)
        kb /= 1024.0
    return "%.1f TB" % kb

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
    print("%6s %-8s %6s %6s %8s %8s COMMAND" % ('PID', 'USER', 'CPU%', 'MEM%', 'RSS', 'VSZ'))
    for proc in sorted(processes, key=lambda x: x['cpu%'], reverse=True):
        print("%6s %-8s %6.1f %6.1f %8s %8s %s" % (
            proc['pid'],
            proc['user'],
            proc['cpu%'],
            proc['mem%'],
            format_size(proc['rss']),
            format_size(proc['vsz']),
            proc['cmd']
        ))
    
    # Print summary
    print("\n=== SSH Process Resource Summary ===")
    print("Total SSH processes: %d" % totals['count'])
    print("Total CPU usage: %.1f%%" % totals['cpu%'])
    print("Total Memory usage: %.1f%%" % totals['mem%'])
    print("Total Resident Memory (RSS): %s" % format_size(totals['rss_kb']))
    print("Total Virtual Memory (VSZ): %s" % format_size(totals['vsz_kb']))

if __name__ == "__main__":
    main()
