# main.py
# The CLI (Command Line Interface) entry point for the telecom analytics tool.
# Users can run queries and manage data directly from the terminal.

import sys
from cmd import Cmd

from analytics.network_event_analytics import NetworkEventAnalytics
from core.config import get_settings
from database.clickhouse_client import ClickHouseClient
from partition_manager.partition_manager import PartitionManager
from repositories.network_event_repository import NetworkEventRepository


class ClickHouseCLI(Cmd):
    """
    Interactive CLI for ClickHouse Telecom Analytics.

    This is the terminal-based interface. Users type commands
    and get results printed as tables or formatted text.
    """

    intro = """
    ╔══════════════════════════════════════════════════════════════╗
    ║       CLICKHOUSE TELECOM ANALYTICS - CLI                     ║
    ║                                                              ║
    ║  Type 'help' for list of commands                            ║
    ║  Type 'help <command>' for command details                   ║
    ║  Type 'exit' or 'quit' to exit                               ║
    ╚══════════════════════════════════════════════════════════════╝
    """
    prompt = "telecom> "

    def __init__(self):
        super().__init__()

        # Load settings from config
        self.settings = get_settings()

        # Connect to ClickHouse using the singleton instance
        print("⏳ Connecting to ClickHouse...")

        self.db = ClickHouseClient.get_instance()

        # Initialize all the layers we need
        self.repo = NetworkEventRepository(self.db)
        self.analytics = NetworkEventAnalytics(self.db)
        self.partition = PartitionManager(self.db)

        # Test the connection and show total events
        try:
            total = self.repo.count()
            print(f"✅ Connected successfully! Total events: {total:,}")
        except Exception as err:
            print(f"❌ Connection failed: {err}")
            sys.exit(1)

    # ------------------------------------------------------------------
    # BASIC COMMANDS - View data and get information
    # ------------------------------------------------------------------

    def do_count(self, _arg):
        """Show total number of events"""
        try:
            total = self.repo.count()
            print(f"📊 Total events: {total:,}")
        except Exception as err:
            print(f"❌ Error: {err}")

    def do_sample(self, arg):
        """Show sample events. Usage: sample [number]"""
        try:
            limit = int(arg) if arg else 5
            rows = self.repo.get_sample(limit)

            if not rows:
                print("⚠️  No data found")
                return

            # Format the data as a nice table
            headers = ["Time", "User", "Type", "City", "Device", "Network", "App", "Latency", "Speed", "Packet Loss"]
            table = []
            for row in rows:
                table.append([
                    row[0].strftime("%Y-%m-%d %H:%M:%S") if row[0] else "N/A",
                    row[1],
                    row[2],
                    row[4],
                    row[5],
                    row[6],
                    row[7],
                    f"{row[8]}ms",
                    f"{row[9]} Mbps",
                    f"{row[10]}%"
                ])

            print(tabulate(table, headers=headers, tablefmt="grid"))

        except Exception as err:
            print(f"❌ Error: {err}")

    def do_user(self, arg):
        """Show events for a specific user. Usage: user <user_id>"""
        if not arg:
            print("⚠️  Please provide user_id. Usage: user 12345")
            return

        try:
            user_id = int(arg)
            rows = self.repo.get_by_user_id(user_id, limit=20)

            if not rows:
                print(f"⚠️  No events found for user {user_id}")
                return

            # Show user statistics
            stats = self.repo.get_stats_by_user(user_id)
            print(f"\n👤 User: {user_id}")
            print(f"   Total Events: {stats['total_events']}")
            print(f"   Avg Latency: {stats['avg_latency_ms']:.2f} ms")
            print(f"   Avg Speed: {stats['avg_download_speed_mbps']:.2f} Mbps")
            print(f"   Avg Packet Loss: {stats['avg_packet_loss_pct']:.2f}%\n")

            # Show recent events
            headers = ["Time", "Type", "City", "App", "Latency", "Speed"]
            table = []
            for row in rows[:10]:
                table.append([
                    row[0].strftime("%Y-%m-%d %H:%M:%S") if row[0] else "N/A",
                    row[2],
                    row[4],
                    row[7],
                    f"{row[8]}ms",
                    f"{row[9]} Mbps"
                ])

            print(tabulate(table, headers=headers, tablefmt="grid"))

        except ValueError:
            print("❌ Invalid user_id. Please provide a number.")
        except Exception as err:
            print(f"❌ Error: {err}")

    def do_latest(self, arg):
        """Show latest events. Usage: latest [number]"""
        try:
            limit = int(arg) if arg else 10
            rows = self.repo.get_latest(limit)

            if not rows:
                print("⚠️  No data found")
                return

            headers = ["Time", "User", "Type", "City", "App", "Latency", "Speed"]
            table = []
            for row in rows:
                table.append([
                    row[0].strftime("%Y-%m-%d %H:%M:%S") if row[0] else "N/A",
                    row[1],
                    row[2],
                    row[4],
                    row[7],
                    f"{row[8]}ms",
                    f"{row[9]} Mbps"
                ])

            print(tabulate(table, headers=headers, tablefmt="grid"))

        except Exception as err:
            print(f"❌ Error: {err}")

    def do_info(self, _arg):
        """Show table information - schema, size, date range, distinct values"""
        try:
            info = self.repo.get_table_info()
            date_range = self.repo.get_date_range()

            print("\n📁 Table Information:")
            print(f"   Name: {info['name']}")
            print(f"   Engine: {info['engine']}")
            print(f"   Total Rows: {info['total_rows']:,}")
            print(f"   Size: {info['total_size_human']}")

            if date_range['min_date'] and date_range['max_date']:
                print(f"   Date Range: {date_range['min_date']} to {date_range['max_date']}")

            # Show what values exist in key columns
            print("\n🏷️  Distinct Values:")
            cities = self.repo.get_distinct_values('city')
            print(f"   Cities: {', '.join(cities)}")

            event_types = self.repo.get_distinct_values('event_type')
            print(f"   Event Types: {', '.join(event_types)}")

            apps = self.repo.get_distinct_values('app_name')
            print(f"   Apps: {', '.join(apps[:5])}{'...' if len(apps) > 5 else ''}")

        except Exception as err:
            print(f"❌ Error: {err}")

    # ------------------------------------------------------------------
    # PARTITION COMMANDS - Manage table partitions
    # ------------------------------------------------------------------

    def do_partition_create(self, _arg):
        """Create a partitioned table"""
        self.partition.create_partitioned_table()

    def do_partition_migrate(self, _arg):
        """Migrate data to partitioned table"""
        self.partition.migrate_to_partitioned()

    def do_partition_replace(self, _arg):
        """Replace original with partitioned table"""
        self.partition.replace_with_partitioned()

    def do_partition_show(self, _arg):
        """Show partition information"""
        self.partition.show_partitions()

    def do_partition_drop(self, arg):
        """Drop a specific partition. Usage: partition_drop 202401"""
        if not arg:
            print("⚠️  Please provide partition value. Usage: partition_drop 202401")
            return
        self.partition.drop_partition(arg)

    def do_partition_clean(self, arg):
        """Drop partitions older than N months. Usage: partition_clean 6"""
        try:
            months = int(arg) if arg else 6
            self.partition.drop_partitions_older_than(months)
        except ValueError:
            print("❌ Please provide a valid number. Usage: partition_clean 6")

    def do_partition_status(self, _arg):
        """Show table status - original and partitioned tables"""
        status = self.partition.get_table_status()
        print("\n📊 Table Status:")
        print("-" * 50)

        if status["original"]:
            print("Original Table:")
            print(f"  Name: {status['original']['name']}")
            print(f"  Engine: {status['original']['engine']}")
            print(f"  Rows: {status['original']['rows']:,}")
            print(f"  Size: {status['original']['size']}")

        if status["partitioned_exists"]:
            print("\nPartitioned Table:")
            print(f"  Name: {status['partitioned']['name']}")
            print(f"  Engine: {status['partitioned']['engine']}")
            print(f"  Rows: {status['partitioned']['rows']:,}")
            print(f"  Size: {status['partitioned']['size']}")

    # ------------------------------------------------------------------
    # ANALYTICS COMMANDS - Reports and insights
    # ------------------------------------------------------------------

    def do_top_apps(self, arg):
        """Show top applications by usage. Usage: top_apps [limit]"""
        try:
            limit = int(arg) if arg else 10
            results = self.analytics.get_top_applications(limit)

            if not results:
                print("⚠️  No data found")
                return

            headers = ["App", "Event Count", "Avg Latency (ms)", "Avg Speed (Mbps)"]
            table = []
            for row in results:
                table.append([row[0], row[1], f"{row[2]:.2f}", f"{row[3]:.2f}"])

            print(f"\n📱 Top {limit} Applications:")
            print(tabulate(table, headers=headers, tablefmt="grid"))

        except Exception as err:
            print(f"❌ Error: {err}")

    def do_top_cities(self, arg):
        """Show top cities by traffic. Usage: top_cities [limit]"""
        try:
            limit = int(arg) if arg else 10
            results = self.analytics.get_top_cities_by_traffic(limit)

            if not results:
                print("⚠️  No data found")
                return

            headers = ["City", "Event Count", "Avg Latency (ms)", "Avg Speed (Mbps)"]
            table = []
            for row in results:
                table.append([row[0], row[1], f"{row[2]:.2f}", f"{row[3]:.2f}"])

            print(f"\n🏙️  Top {limit} Cities:")
            print(tabulate(table, headers=headers, tablefmt="grid"))

        except Exception as err:
            print(f"❌ Error: {err}")

    def do_network_quality(self, _arg):
        """Show network quality report by network type"""
        try:
            results = self.analytics.get_network_quality_report()

            if not results:
                print("⚠️  No data found")
                return

            headers = ["Network", "Event Count", "Avg Latency (ms)", "Avg Speed (Mbps)", "Avg Packet Loss (%)"]
            table = []
            for row in results:
                table.append([row[0], row[1], f"{row[2]:.2f}", f"{row[3]:.2f}", f"{row[4]:.2f}"])

            print("\n📶 Network Quality Report:")
            print(tabulate(table, headers=headers, tablefmt="grid"))

        except Exception as err:
            print(f"❌ Error: {err}")

    def do_daily_report(self, arg):
        """Show daily events report. Usage: daily_report [days]"""
        try:
            days = int(arg) if arg else 7
            results = self.analytics.get_daily_events_report(days)

            if not results:
                print("⚠️  No data found")
                return

            headers = ["Date", "Event Count", "Avg Latency (ms)", "Avg Speed (Mbps)"]
            table = []
            for row in results:
                table.append([row[0], row[1], f"{row[2]:.2f}", f"{row[3]:.2f}"])

            print(f"\n📅 Daily Report (Last {days} days):")
            print(tabulate(table, headers=headers, tablefmt="grid"))

        except Exception as err:
            print(f"❌ Error: {err}")

    def do_hourly_heatmap(self, _arg):
        """Show hourly event distribution with a visual bar chart"""
        try:
            results = self.analytics.get_hourly_heatmap()

            if not results:
                print("⚠️  No data found")
                return

            print("\n🕐 Hourly Event Distribution:")
            print("Hour | Count | Bar")
            print("-----|-------|----------------------------------------")
            max_count = max([r[1] for r in results]) if results else 1
            for hour, count in results:
                bar = "█" * min(int(count / max_count * 50), 50)
                print(f"{hour:4} | {count:5} | {bar}")

        except Exception as err:
            print(f"❌ Error: {err}")

    def do_device_stats(self, _arg):
        """Show device statistics"""
        try:
            results = self.analytics.get_device_statistics()

            if not results:
                print("⚠️  No data found")
                return

            headers = ["Device", "Event Count", "Avg Latency (ms)", "Avg Speed (Mbps)"]
            table = []
            for row in results:
                table.append([row[0], row[1], f"{row[2]:.2f}", f"{row[3]:.2f}"])

            print("\n📱 Device Statistics:")
            print(tabulate(table, headers=headers, tablefmt="grid"))

        except Exception as err:
            print(f"❌ Error: {err}")

    # ------------------------------------------------------------------
    # CUSTOM QUERY - Run raw SQL
    # ------------------------------------------------------------------

    def do_query(self, arg):
        """Execute custom SQL query. Usage: query <SQL>"""
        if not arg:
            print("⚠️  Please provide SQL query. Usage: query SELECT * FROM ...")
            return

        try:
            result = self.db.query(arg)

            if result.result_rows:
                headers = [col[0] for col in result.column_names]
                print(tabulate(result.result_rows, headers=headers, tablefmt="grid"))
                print(f"\n✅ {len(result.result_rows)} rows returned")
            else:
                print("✅ Query executed successfully (no results)")

        except Exception as err:
            print(f"❌ Query error: {err}")

    # ------------------------------------------------------------------
    # SYSTEM COMMANDS
    # ------------------------------------------------------------------

    def do_clear(self, _arg):
        """Clear the screen"""
        import os
        os.system('cls' if os.name == 'nt' else 'clear')

    def do_exit(self, _arg):
        """Exit the CLI"""
        print("👋 Goodbye!")
        self.db.close()
        return True

    def do_quit(self, _arg):
        """Exit the CLI"""
        return self.do_exit(_arg)

    # ------------------------------------------------------------------
    # HELP - Show available commands
    # ------------------------------------------------------------------

    def help_commands(self):
        """List all available commands"""
        commands = [
            # Basic commands
            ("count", "Show total number of events"),
            ("sample [n]", "Show n sample events (default: 5)"),
            ("user <id>", "Show events and stats for a user"),
            ("latest [n]", "Show n latest events (default: 10)"),
            ("info", "Show table information"),

            # Analytics commands
            ("top_apps [n]", "Show top n applications (default: 10)"),
            ("top_cities [n]", "Show top n cities (default: 10)"),
            ("network_quality", "Show network quality report"),
            ("daily_report [n]", "Show daily report for last n days (default: 7)"),
            ("hourly_heatmap", "Show hourly event distribution"),
            ("device_stats", "Show device statistics"),

            # Partition commands
            ("partition_status", "Show table and partition status"),
            ("partition_create", "Create a partitioned table"),
            ("partition_migrate", "Migrate data to partitioned table"),
            ("partition_replace", "Replace original with partitioned table"),
            ("partition_show", "Show partition information"),
            ("partition_drop <YYYYMM>", "Drop a specific partition (e.g., 202401)"),
            ("partition_clean <months>", "Drop partitions older than N months (default: 6)"),
            ("partition_merge", "Optimize table by merging partitions"),

            # Utility commands
            ("query <SQL>", "Execute custom SQL query"),
            ("clear", "Clear the screen"),
            ("exit/quit", "Exit the CLI"),
        ]

        print("\n📋 Available Commands:")
        print("-" * 60)
        print("  BASIC COMMANDS:")
        for cmd, desc in commands[:5]:
            print(f"    {cmd:20} {desc}")

        print("\n  ANALYTICS COMMANDS:")
        for cmd, desc in commands[5:11]:
            print(f"    {cmd:20} {desc}")

        print("\n  PARTITION COMMANDS:")
        for cmd, desc in commands[11:19]:
            print(f"    {cmd:20} {desc}")

        print("\n  UTILITY COMMANDS:")
        for cmd, desc in commands[19:]:
            print(f"    {cmd:20} {desc}")

        print("-" * 60)
        print("💡 Type 'help <command>' for detailed usage")

    def do_help(self, arg):
        """Show help for commands"""
        if arg:
            method = getattr(self, f"do_{arg}", None)
            if method and method.__doc__:
                print(f"\n📖 {method.__doc__}")
            else:
                print(f"⚠️  No help available for '{arg}'")
        else:
            self.help_commands()


# ------------------------------------------------------------------
# ENTRY POINT
# ------------------------------------------------------------------

if __name__ == "__main__":
    try:
        from tabulate import tabulate

        ClickHouseCLI().cmdloop()
    except ImportError:
        print("⚠️  'tabulate' not installed. Installing...")
        import subprocess

        subprocess.check_call([sys.executable, "-m", "pip", "install", "tabulate"])
        print("✅ tabulate installed. Please restart the CLI.")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        sys.exit(1)
