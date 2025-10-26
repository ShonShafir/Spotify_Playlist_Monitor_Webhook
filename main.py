import monitor_playlist

def main():
    print("Checking for playlist update...")
    monitor_playlist.monitor_playlist()
    print("Done!")

if __name__ == '__main__':
    main()
