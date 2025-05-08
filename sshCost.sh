#!/bin/bash
# Garland Joseph
# ssh cost shell script
# ----

#!/bin/bash

# Function to format size in human-readable format
format_size() {
    local kb=$1
    local unit="KB"
    
    if (( $(echo "$kb >= 1024" | bc -l) )); then
        kb=$(echo "scale=1; $kb / 1024" | bc)
        unit="MB"
    fi
    
    if (( $(echo "$kb >= 1024" | bc -l) )); then
        kb=$(echo "scale=1; $kb / 1024" | bc)
        unit="GB"
    fi
    
    if (( $(echo "$kb >= 1024" | bc -l) )); then
        kb=$(echo "scale=1; $kb / 1024" | bc)
        unit="TB"
    fi
    
    echo "$kb $unit"
}

# Function to get SSH processes
get_ssh_processes() {
    local ssh_processes=()
    local line
    
    # Read ps output line by line
    while read -r line; do
        # Skip header and grep/ps lines
        if [[ "$line" =~ [sS][sS][hH] ]] && 
           ! [[ "$line" =~ grep ]] && 
           ! [[ "$line" =~ "ps -eo" ]]; then
            # Parse the line into components
            read -r pid user pcpu pmem rss vsz cmd <<< "$line"
            
            # Add to processes array
            ssh_processes+=("$pid|$user|$pcpu|$pmem|$rss|$vsz|$cmd")
        fi
    done < <(ps -eo pid,user,pcpu,pmem,rss,vsz,cmd)
    
    echo "${ssh_processes[@]}"
}

# Function to calculate totals
calculate_totals() {
    local processes=("$@")
    local count=0
    local cpu_total=0
    local mem_total=0
    local rss_total=0
    local vsz_total=0
    
    for proc in "${processes[@]}"; do
        IFS='|' read -r pid user pcpu pmem rss vsz cmd <<< "$proc"
        count=$((count + 1))
        cpu_total=$(echo "$cpu_total + $pcpu" | bc)
        mem_total=$(echo "$mem_total + $pmem" | bc)
        rss_total=$((rss_total + rss))
        vsz_total=$((vsz_total + vsz))
    done
    
    echo "$count|$cpu_total|$mem_total|$rss_total|$vsz_total"
}

# Main function
main() {
    echo "Analyzing SSH processes..."
    echo
    
    # Get all SSH processes
    processes=($(get_ssh_processes))
    
    if [ ${#processes[@]} -eq 0 ]; then
        echo "No SSH processes found."
        return
    fi
    
    # Calculate totals
    IFS='|' read -r count cpu_total mem_total rss_total vsz_total <<< "$(calculate_totals "${processes[@]}")"
    
    # Print header
    printf "%6s %-8s %6s %6s %8s %8s COMMAND\n" "PID" "USER" "CPU%" "MEM%" "RSS" "VSZ"
    
    # Print processes sorted by CPU% (descending)
    for proc in "${processes[@]}"; do
        IFS='|' read -r pid user pcpu pmem rss vsz cmd <<< "$proc"
        printf "%6s %-8s %6.1f %6.1f %8s %8s %s\n" \
               "$pid" \
               "$user" \
               "$pcpu" \
               "$pmem" \
               "$(format_size "$rss")" \
               "$(format_size "$vsz")" \
               "$cmd"
    done | sort -k3 -nr
    
    # Print summary
    echo
    echo "=== SSH Process Resource Summary ==="
    echo "Total SSH processes: $count"
    printf "Total CPU usage: %.1f%%\n" "$cpu_total"
    printf "Total Memory usage: %.1f%%\n" "$mem_total"
    echo "Total Resident Memory (RSS): $(format_size "$rss_total")"
    echo "Total Virtual Memory (VSZ): $(format_size "$vsz_total")"
}

# Run main function
main
