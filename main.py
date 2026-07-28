import sys
from cmd import Cmd
from analytics.network_event_analytics import NetworkEventAnalytics
from config import *
from database.clickhouse_client import ClickHouseClient
from repositories.network_event_repository import NetworkEventRepository


class ClickHouseCLI(Cmd):
    """Interactive CLI for ClickHouse Telecom Analytics"""

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

        # Initialize connections
        print("⏳ Connecting to ClickHouse...")
        self.db = ClickHouseClient(
            host=CLICKHOUSE_HOST,
            port=CLICKHOUSE_PORT,
            database=CLICKHOUSE_DATABASE,
            username=CLICKHOUSE_USERNAME,
            password=CLICKHOUSE_PASSWORD,
        )
        self.repo = NetworkEventRepository(self.db.client)
        self.analytics = NetworkEventAnalytics(self.db.client)

        # Check connection
        try:
            total = self.repo.count()
            print(f"✅ Connected successfully! Total events: {total:,}")
        except Exception as err:
            print(f"❌ Connection failed: {err}")
            sys.exit(1)

    # ============================================
    # BASIC COMMANDS
    # ============================================

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

            # Stats
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

    def do_info(self, arg):
        """Show table information"""
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

            # Distinct values
            print("\n🏷️  Distinct Values:")
            cities = self.repo.get_distinct_values('city')
            print(f"   Cities: {', '.join(cities)}")

            event_types = self.repo.get_distinct_values('event_type')
            print(f"   Event Types: {', '.join(event_types)}")

            apps = self.repo.get_distinct_values('app_name')
            print(f"   Apps: {', '.join(apps[:5])}{'...' if len(apps) > 5 else ''}")

        except Exception as err:
            print(f"❌ Error: {err}")

    # ============================================
    # ANALYTICS COMMANDS
    # ============================================

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

    def do_network_quality(self, arg):
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

    def do_hourly_heatmap(self, arg):
        """Show hourly event distribution"""
        try:
            results = self.analytics.get_hourly_heatmap()

            if not results:
                print("⚠️  No data found")
                return

            print("\n🕐 Hourly Event Distribution:")
            print("Hour | Count | Bar")
            print("-----|-------|----------------------------------------")
            for hour, count in results:
                bar = "█" * min(int(count / max(1, max([r[1] for r in results])) * 50), 50)
                print(f"{hour:4} | {count:5} | {bar}")

        except Exception as err:
            print(f"❌ Error: {err}")

    def do_device_stats(self, arg):
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

    # ============================================
    # CUSTOM QUERY
    # ============================================

    def do_query(self, arg):
        """Execute custom SQL query. Usage: query <SQL>"""
        if not arg:
            print("⚠️  Please provide SQL query. Usage: query SELECT * FROM ...")
            return

        try:
            result = self.db.client.query(arg)

            if result.result_rows:
                headers = [col[0] for col in result.column_names]
                print(tabulate(result.result_rows, headers=headers, tablefmt="grid"))
                print(f"\n✅ {len(result.result_rows)} rows returned")
            else:
                print("✅ Query executed successfully (no results)")

        except Exception as err:
            print(f"❌ Query error: {err}")

    # ============================================
    # SYSTEM COMMANDS
    # ============================================
    @staticmethod
    def do_clear(self, arg):
        """Clear the screen"""
        import os
        os.system('cls' if os.name == 'nt' else 'clear')

    def do_exit(self, arg):
        """Exit the CLI"""
        print("👋 Goodbye!")
        self.db.close()
        return True

    def do_quit(self, arg):
        """Exit the CLI"""
        return self.do_exit(arg)

    # ============================================
    # HELP
    # ============================================
    def help_commands(self):
        """List all available commands"""
        commands = [
            ("count", "Show total number of events"),
            ("sample [n]", "Show n sample events (default: 5)"),
            ("user <id>", "Show events and stats for a user"),
            ("latest [n]", "Show n latest events (default: 10)"),
            ("info", "Show table information"),
            ("top_apps [n]", "Show top n applications (default: 10)"),
            ("top_cities [n]", "Show top n cities (default: 10)"),
            ("network_quality", "Show network quality report"),
            ("daily_report [n]", "Show daily report for last n days (default: 7)"),
            ("hourly_heatmap", "Show hourly event distribution"),
            ("device_stats", "Show device statistics"),
            ("query <SQL>", "Execute custom SQL query"),
            ("clear", "Clear the screen"),
            ("exit/quit", "Exit the CLI"),
        ]

        print("\n📋 Available Commands:")
        print("-" * 60)
        for cmd, desc in commands:
            print(f"  {cmd:20} {desc}")
        print("-" * 60)

    def do_help(self, arg):
        """Show help for commands"""
        if arg:
            # Show help for specific command
            method = getattr(self, f"do_{arg}", None)
            if method and method.__doc__:
                print(f"\n{method.__doc__}")
            else:
                print(f"⚠️  No help available for '{arg}'")
        else:
            self.help_commands()


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
