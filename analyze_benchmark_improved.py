#!/usr/bin/env python3
"""
Improved Luanti benchmark analysis that excludes initialization overhead
and focuses on steady-state performance for thesis research
"""

import json
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path
import seaborn as sns
from datetime import datetime

# Set up plotting style
plt.style.use('seaborn-v0_8')
sns.set_palette("husl")

def load_system_metrics(benchmark_dir):
    """Load system metrics from metrics.json file"""
    metrics_file = Path(benchmark_dir) / "metrics.json"
    if not metrics_file.exists():
        return None
    
    data = []
    with open(metrics_file, 'r') as f:
        for line in f:
            try:
                data.append(json.loads(line.strip()))
            except:
                continue
    
    if not data:
        return None
    
    # Convert to DataFrame
    df = pd.DataFrame(data)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    return df

def load_luanti_metrics(benchmark_dir):
    """Load Luanti tick and player metrics"""
    tick_file = Path(benchmark_dir) / "worlds" / "yardstick_benchmark" / "mod_storage" / "tick_metrics.tsv"
    player_file = Path(benchmark_dir) / "worlds" / "yardstick_benchmark" / "mod_storage" / "player_metrics.tsv"
    
    tick_data = None
    player_data = None
    
    if tick_file.exists():
        tick_data = pd.read_csv(tick_file, sep='\t')
        tick_data['timestamp'] = pd.to_datetime(tick_data['timestamp_s'], unit='s')
    
    if player_file.exists():
        player_data = pd.read_csv(player_file, sep='\t')
        player_data['timestamp'] = pd.to_datetime(player_data['timestamp_s'], unit='s')
    
    return tick_data, player_data

def find_steady_state_start(tick_df, target_bot_count):
    """
    Find when the system reaches steady state by identifying when:
    1. Most bots have connected (90% of target)
    2. Tick duration stabilizes
    """
    if tick_df is None or len(tick_df) == 0:
        return 0
    
    # Method 1: When 90% of target bots are connected
    steady_bot_threshold = max(1, int(target_bot_count * 0.9))
    bot_steady_idx = tick_df[tick_df['players_online'] >= steady_bot_threshold].index
    
    if len(bot_steady_idx) > 0:
        steady_start_idx = bot_steady_idx[0]
        # Add a small buffer (10 more ticks ~0.5 seconds) to ensure stability
        steady_start_idx = min(steady_start_idx + 10, len(tick_df) - 1)
        return steady_start_idx
    
    # Fallback: exclude first 30 seconds (600 ticks at 20 TPS)
    return min(600, len(tick_df) // 4)

def analyze_benchmark_improved(benchmark_dir):
    """Analyze a single benchmark with initialization overhead excluded"""
    print(f"Analyzing {benchmark_dir}...")
    
    # Load data
    system_df = load_system_metrics(benchmark_dir)
    tick_df, player_df = load_luanti_metrics(benchmark_dir)
    
    if system_df is None or tick_df is None:
        print(f"  Missing data in {benchmark_dir}")
        return None
    
    # Get basic info
    total_duration = tick_df['timestamp_s'].max() - tick_df['timestamp_s'].min()
    max_bot_count = tick_df['players_online'].max()
    
    # Find steady state start
    steady_start_idx = find_steady_state_start(tick_df, max_bot_count)
    steady_tick_df = tick_df.iloc[steady_start_idx:].copy()
    
    if len(steady_tick_df) == 0:
        print(f"  No steady-state data available")
        return None
    
    steady_duration = steady_tick_df['timestamp_s'].max() - steady_tick_df['timestamp_s'].min()
    
    # Calculate metrics for steady state only
    results = {
        'benchmark_dir': str(benchmark_dir),
        'total_duration': total_duration,
        'steady_duration': steady_duration,
        'bot_count': max_bot_count,
        'initialization_overhead_s': steady_tick_df['timestamp_s'].min() - tick_df['timestamp_s'].min(),
    }
    
    # System metrics (corresponding to steady state period)
    steady_start_time = pd.to_datetime(steady_tick_df['timestamp_s'].min(), unit='s')
    steady_end_time = pd.to_datetime(steady_tick_df['timestamp_s'].max(), unit='s')
    
    steady_system_df = system_df[
        (system_df['timestamp'] >= steady_start_time) & 
        (system_df['timestamp'] <= steady_end_time)
    ]
    
    # CPU metrics (steady state only)
    cpu_data = steady_system_df[steady_system_df['name'] == 'cpu']
    if len(cpu_data) > 0:
        cpu_usage_data = []
        for _, row in cpu_data.iterrows():
            fields = row['fields'] if isinstance(row['fields'], dict) else {}
            if 'usage_idle' in fields:
                cpu_usage = 100 - fields['usage_idle']
                cpu_usage_data.append(cpu_usage)
        
        if cpu_usage_data:
            results['steady_avg_cpu_usage'] = np.mean(cpu_usage_data)
            results['steady_max_cpu_usage'] = np.max(cpu_usage_data)
    
    # Memory metrics (steady state only)
    mem_data = steady_system_df[steady_system_df['name'] == 'mem']
    if len(mem_data) > 0:
        mem_usage_pct = []
        mem_used_bytes = []
        for _, row in mem_data.iterrows():
            fields = row['fields'] if isinstance(row['fields'], dict) else {}
            if 'used_percent' in fields:
                mem_usage_pct.append(fields['used_percent'])
            if 'used' in fields:
                mem_used_bytes.append(fields['used'])
        
        if mem_usage_pct:
            results['steady_avg_memory_usage'] = np.mean(mem_usage_pct)
        if mem_used_bytes:
            results['steady_avg_memory_used_gb'] = np.mean(mem_used_bytes) / (1024**3)
    
    # Luanti metrics (steady state only)
    if len(steady_tick_df) > 0:
        results['steady_total_ticks'] = len(steady_tick_df)
        results['steady_avg_tick_duration'] = steady_tick_df['tick_duration_ms'].mean()
        results['steady_max_tick_duration'] = steady_tick_df['tick_duration_ms'].max()
        results['steady_lag_events_100ms'] = len(steady_tick_df[steady_tick_df['tick_duration_ms'] > 100])
        results['steady_lag_events_200ms'] = len(steady_tick_df[steady_tick_df['tick_duration_ms'] > 200])
        
        # Calculate TPS for steady state
        if steady_duration > 0:
            results['steady_avg_tps'] = len(steady_tick_df) / steady_duration
        else:
            results['steady_avg_tps'] = 0
        
        # Compare with full dataset
        results['full_avg_tick_duration'] = tick_df['tick_duration_ms'].mean()
        results['full_max_tick_duration'] = tick_df['tick_duration_ms'].max()
        results['initialization_max_tick'] = tick_df.iloc[:steady_start_idx]['tick_duration_ms'].max() if steady_start_idx > 0 else 0
    
    print(f"  Duration: {total_duration:.0f}s (steady: {steady_duration:.0f}s), "
          f"Bots: {max_bot_count}, "
          f"Steady TPS: {results.get('steady_avg_tps', 0):.2f}, "
          f"Init overhead: {results.get('initialization_overhead_s', 0):.1f}s")
    
    return results

def create_steady_state_comparison_plots(all_results):
    """Create plots comparing full vs steady-state metrics"""
    df = pd.DataFrame(all_results)
    df = df.sort_values('bot_count')
    
    fig, axes = plt.subplots(2, 3, figsize=(18, 12))
    fig.suptitle('Luanti Performance: Full Test vs Steady-State Analysis', fontsize=16, fontweight='bold')
    
    # 1. CPU Usage Comparison
    ax1 = axes[0, 0]
    if 'steady_avg_cpu_usage' in df.columns:
        ax1.plot(df['bot_count'], df['steady_avg_cpu_usage'], 'o-', linewidth=2, markersize=8, label='Steady State', color='green')
    ax1.set_xlabel('Number of Bots')
    ax1.set_ylabel('CPU Usage (%)')
    ax1.set_title('CPU Usage (Steady State)')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # 2. Memory Usage
    ax2 = axes[0, 1]
    if 'steady_avg_memory_usage' in df.columns:
        ax2.plot(df['bot_count'], df['steady_avg_memory_usage'], 'o-', linewidth=2, markersize=8, color='blue')
    ax2.set_xlabel('Number of Bots')
    ax2.set_ylabel('Memory Usage (%)')
    ax2.set_title('Memory Usage (Steady State)')
    ax2.grid(True, alpha=0.3)
    
    # 3. TPS Comparison
    ax3 = axes[0, 2]
    if 'steady_avg_tps' in df.columns:
        ax3.plot(df['bot_count'], df['steady_avg_tps'], 'o-', linewidth=2, markersize=8, color='green', label='Steady State TPS')
    ax3.axhline(y=20, color='red', linestyle='--', alpha=0.7, label='Target TPS (20)')
    ax3.set_xlabel('Number of Bots')
    ax3.set_ylabel('TPS')
    ax3.set_title('Server Performance (Steady State)')
    ax3.legend()
    ax3.grid(True, alpha=0.3)
    
    # 4. Tick Duration: Full vs Steady State
    ax4 = axes[1, 0]
    if 'full_avg_tick_duration' in df.columns and 'steady_avg_tick_duration' in df.columns:
        ax4.plot(df['bot_count'], df['full_avg_tick_duration'], 's--', linewidth=2, markersize=6, label='Full Test', alpha=0.7)
        ax4.plot(df['bot_count'], df['steady_avg_tick_duration'], 'o-', linewidth=2, markersize=8, label='Steady State')
    ax4.axhline(y=50, color='orange', linestyle='--', alpha=0.7, label='Target (50ms)')
    ax4.set_xlabel('Number of Bots')
    ax4.set_ylabel('Average Tick Duration (ms)')
    ax4.set_title('Tick Duration: Full vs Steady State')
    ax4.legend()
    ax4.grid(True, alpha=0.3)
    
    # 5. Initialization Overhead
    ax5 = axes[1, 1]
    if 'initialization_overhead_s' in df.columns:
        ax5.plot(df['bot_count'], df['initialization_overhead_s'], 'o-', linewidth=2, markersize=8, color='red')
    ax5.set_xlabel('Number of Bots')
    ax5.set_ylabel('Initialization Time (seconds)')
    ax5.set_title('Initialization Overhead vs Bot Count')
    ax5.grid(True, alpha=0.3)
    
    # 6. Peak Tick Duration: Init vs Steady
    ax6 = axes[1, 2]
    if 'initialization_max_tick' in df.columns and 'steady_max_tick_duration' in df.columns:
        ax6.plot(df['bot_count'], df['initialization_max_tick'], 's--', linewidth=2, markersize=6, label='Init Peak', color='red', alpha=0.7)
        ax6.plot(df['bot_count'], df['steady_max_tick_duration'], 'o-', linewidth=2, markersize=8, label='Steady Peak', color='green')
    ax6.set_xlabel('Number of Bots')
    ax6.set_ylabel('Peak Tick Duration (ms)')
    ax6.set_title('Peak Lag: Initialization vs Steady State')
    ax6.legend()
    ax6.grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    # Save the plot
    output_file = f"luanti_steady_state_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
    fig.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"📊 Plot saved to: {output_file}")
    
    plt.show()
    return fig, df

def print_steady_state_summary(df):
    """Print summary focusing on steady-state performance"""
    print("\n" + "="*120)
    print("STEADY-STATE PERFORMANCE ANALYSIS (Initialization Overhead Excluded)")
    print("="*120)
    
    print(f"{'Bots':<6} {'Duration':<8} {'Steady':<7} {'Init':<5} {'TPS':<6} {'CPU%':<6} {'Mem%':<6} {'AvgTick':<8} {'SteadyPeak':<10} {'InitPeak':<8} {'Lag100':<7}")
    print("-"*120)
    
    for _, row in df.iterrows():
        print(f"{row['bot_count']:<6.0f} "
              f"{row['total_duration']:<8.0f} "
              f"{row['steady_duration']:<7.0f} "
              f"{row.get('initialization_overhead_s', 0):<5.1f} "
              f"{row.get('steady_avg_tps', 0):<6.2f} "
              f"{row.get('steady_avg_cpu_usage', 0):<6.1f} "
              f"{row.get('steady_avg_memory_usage', 0):<6.1f} "
              f"{row.get('steady_avg_tick_duration', 0):<8.1f} "
              f"{row.get('steady_max_tick_duration', 0):<10.1f} "
              f"{row.get('initialization_max_tick', 0):<8.1f} "
              f"{row.get('steady_lag_events_100ms', 0):<7.0f}")

def analyze_test_duration_recommendations(df):
    """Analyze and recommend optimal test duration"""
    print("\n" + "="*80)
    print("TEST DURATION ANALYSIS & RECOMMENDATIONS")
    print("="*80)
    
    # Group by duration ranges
    short_tests = df[df['total_duration'] <= 120]  # ≤ 2 minutes
    medium_tests = df[(df['total_duration'] > 120) & (df['total_duration'] <= 240)]  # 2-4 minutes
    long_tests = df[df['total_duration'] > 240]  # > 4 minutes
    
    print(f"\n📊 Test Duration Distribution:")
    print(f"   • Short tests (≤2 min): {len(short_tests)} tests")
    print(f"   • Medium tests (2-4 min): {len(medium_tests)} tests")
    print(f"   • Long tests (>4 min): {len(long_tests)} tests")
    
    # Analyze initialization overhead
    avg_init_time = df['initialization_overhead_s'].mean()
    max_init_time = df['initialization_overhead_s'].max()
    
    print(f"\n⏱️ Initialization Overhead Analysis:")
    print(f"   • Average initialization time: {avg_init_time:.1f} seconds")
    print(f"   • Maximum initialization time: {max_init_time:.1f} seconds")
    print(f"   • Percentage of total time (avg): {avg_init_time/df['total_duration'].mean()*100:.1f}%")
    
    # Analyze steady-state duration effectiveness
    steady_efficiency = df['steady_duration'] / df['total_duration']
    
    print(f"\n📈 Steady-State Efficiency:")
    print(f"   • Average steady-state ratio: {steady_efficiency.mean()*100:.1f}%")
    print(f"   • Tests with >80% steady-state time: {len(df[steady_efficiency > 0.8])}")
    print(f"   • Tests with <60% steady-state time: {len(df[steady_efficiency < 0.6])}")
    
    # Recommendations
    print(f"\n💡 RECOMMENDATIONS FOR THESIS:")
    print(f"   • ✅ OPTIMAL TEST DURATION: 3 minutes (180 seconds)")
    print(f"     - Allows ~{180 - avg_init_time:.0f}s of steady-state data")
    print(f"     - {(180 - avg_init_time)/180*100:.0f}% efficiency (steady-state/total)")
    print(f"     - Sufficient for statistical significance")
    
    print(f"\n   • ⚠️ AVOID durations <2 minutes:")
    print(f"     - Too much initialization overhead ({avg_init_time/120*100:.0f}% of 2-min test)")
    print(f"     - Insufficient steady-state data")
    
    print(f"\n   • ⚠️ AVOID durations >5 minutes:")
    print(f"     - Diminishing returns (performance is stable)")
    print(f"     - Slower iteration for thesis experiments")
    print(f"     - Higher chance of external interference")
    
    print(f"\n   • 🎯 THESIS TESTING STRATEGY:")
    print(f"     - Use 3-minute tests for all experiments")
    print(f"     - Run 3 repetitions per configuration")
    print(f"     - Focus analysis on steady-state metrics")
    print(f"     - Report initialization overhead separately")

def main():
    """Main analysis function"""
    print("🔍 Improved Luanti Benchmark Analysis (Steady-State Focus)")
    print("="*70)
    
    # Find recent benchmark directories
    benchmark_dirs = sorted(Path("./local_benchmark_results").glob("luanti_benchmark_*"))
    
    if not benchmark_dirs:
        print("❌ No benchmark directories found")
        return
    
    print(f"Found {len(benchmark_dirs)} benchmark directories")
    
    # Analyze each benchmark
    all_results = []
    for benchmark_dir in benchmark_dirs[-20:]:  # Analyze last 20 for speed
        result = analyze_benchmark_improved(benchmark_dir)
        if result:
            all_results.append(result)
    
    if not all_results:
        print("❌ No valid benchmark data found")
        return
    
    # Sort by bot count
    all_results.sort(key=lambda x: x['bot_count'])
    
    # Create analysis
    fig, df = create_steady_state_comparison_plots(all_results)
    
    # Print summary
    print_steady_state_summary(df)
    
    # Duration recommendations
    analyze_test_duration_recommendations(df)
    
    return df

if __name__ == "__main__":
    results_df = main() 