#nieuwsuur Intstagram Hashtag Tracker en Scraper

import csv
import json
import datetime
from datetime import datetime
from datetime import datetime as dt, timedelta
import re
import time
import random
from instagrapi import Client
from typing import Optional, Tuple, List, Dict, Set
import os
import glob

settings_dir = "Settings"
results_dir = "Results"
max_amount = 27


def ensure_dir(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)

ensure_dir(settings_dir)
ensure_dir(results_dir)


def login_to_instagram() -> Optional[Client]:
    cl = Client()
    session_file = os.path.join(settings_dir, "session.json")
    user_data_file = os.path.join(settings_dir, "session_user.json")

    session_exists = os.path.isfile(session_file)
    user_data_exists = os.path.isfile(user_data_file)

    if session_exists and user_data_exists:
        cl.load_settings(session_file)
        try:
            with open(user_data_file, "r") as f:
                username_data = json.load(f)
                print(f"You are logged in as: {username_data['username']}.")
                return cl
        except Exception as e:
            print("Failed to load session user data:", e)
            # Delete session files
            time.sleep(1)  
            try:
                os.remove(user_data_file)
                print("Session user data file removed.")
            except Exception as remove_error:
                print("Error while trying to remove the file:", remove_error)
            
           
            if not os.path.exists(user_data_file):
                try:
                    with open(user_data_file, "r") as f:
                        username_data = json.load(f)
                        print(f"You are logged in as: {username_data['username']}.")
                        return cl
                except FileNotFoundError:
                    print("Session user data file not found.")
                except Exception as open_error:
                    print("Failed to load session user data after removing the file:", open_error)

    # If session files do not exist or failed to load, attempt login procedure
    return login_procedure(cl)

def login_procedure(cl: Client) -> Optional[Client]:
    print("No session data found. Please log in.")
    username = input("Please enter your Instagram username: ")
    password = input("Please enter your Instagram password: ")
    try:
        cl.login(username, password)
        cl.dump_settings(os.path.join(settings_dir, "session.json"))  
        with open(os.path.join(settings_dir, "session_user.json"), "w") as f:   
            json.dump({"username": username}, f)
        print(f"You are now logged in as: {username}.")
        return cl  # Return the Client instance if login is successful
    except Exception as e:
        print("Login failed:", e)
        return None  # Return None if login fails



def settings_menu(cl: Client):
    global max_amount
    while True:  
        print("\nSettings Menu:")
        print("1. Back")
        print("2. Change max results per fetch")
        print("3. Logout")
        choice = input("Choose an option (1, 2, or 3): ").strip()
        
        if choice == '1':
            break 
        elif choice == '2':
            new_max_amount = input("Enter new max results per fetch: ").strip()
            if new_max_amount.isdigit():
                max_amount = int(new_max_amount)
                print(f"Fetch limit set to: {max_amount}")
            else:
                print("Invalid input. Please enter a number.")
        elif choice == '3':
            logout(cl)
            cl = login_to_instagram() 
            break  
        else:
            print("Invalid choice. Please try again.")

def logout(cl: Client):
    try:
        
        cl.logout()
        print("Logged out successfully.")
    except Exception as e:
        print("Logout failed:", e)

    session_file = os.path.join(settings_dir, "session.json")
    user_data_file = os.path.join(settings_dir, "session_user.json")

    # Delete sessionfiles
    if os.path.exists(session_file):
        os.remove(session_file)
        print("deleting session files.")
    else:
        print("Session file not found.")
    
    if os.path.exists(user_data_file):
        os.remove(user_data_file)
        print("User data file deleted.")
    else:
        print("User data file not found.")





def get_hashtag_info(cl: Client, hashtag: str) -> Dict:
    try:
        hashtag_info = cl.hashtag_info(hashtag)
        if hashtag_info is not None and hasattr(hashtag_info, 'media_count'):
            media_count = hashtag_info.media_count if hashtag_info.media_count is not None else 0
            return {"name": hashtag_info.name, "id": hashtag_info.id, "media_count": media_count}
        else:
            return {"name": hashtag, "id": None, "media_count": 0}
    except Exception as e:
        print(f"Failed to retrieve hashtag info: {e}")
        return {"name": hashtag, "id": None, "media_count": 0}



def get_search_option(media_count: int, show_total_results: bool = True) -> Tuple[int, int, int, Tuple[Optional[dt.date], Optional[dt.date]]]:
    print("\nHow would you like to search for the hashtag?")
    print("1. Collect recent popular posts")
    print("2. Collect all-time popular posts")
    print("3. Collect all available posts (slow)")
    
    while True:
        choice = input("Choose an option (1, 2, or 3): ").strip()
        
        if choice in ['1', '2', '3']:
            post_count = get_post_count(media_count, show_total_results) if choice in ['1', '2'] else media_count
            date_range = get_date_range() if choice == '3' else (None, None)
            return int(choice), post_count, date_range
        else:
            print("Invalid choice. Please enter 1, 2, or 3.")

            continue

        
        date_range = get_date_range()  
        return int(choice), post_count, api_choice, date_range



def get_post_count(media_count: int, show_total_results: bool = True) -> int:
    if show_total_results:
        print(f"\nHow many posts would you like to collect? There are currently {media_count} total results. Choose a maximum number: ")
    else:
        print("\nHow many posts would you like to collect? Choose a maximum number:")
    while True:
        count = input().strip()
        if count.isdigit():
            return int(count)
        else:
            print("Invalid number. Please enter a valid number.")

def calculate_estimated_time(post_count: int, option: int, media_count: int) -> str:
    global max_amount
    
    if media_count is None:
        media_count = 0  

    if option == 3:
        fetches_needed = (media_count / max_amount) * 2
    else:
        fetches_needed = post_count / max_amount

    estimated_seconds = fetches_needed * 5
    estimated_time = str(timedelta(seconds=round(estimated_seconds)))
    return estimated_time


def get_date_range() -> Tuple[Optional[datetime.date], Optional[datetime.date]]:
    choice = input("Would you like to search from a specific start date? (Y/N): ").strip().upper()
    if choice == 'Y':
        start_date_str = input("Please enter the start date in DD-MM-YYYY format: ").strip()
        try:
            start_date = datetime.datetime.strptime(start_date_str, '%d-%m-%Y').date()
            return (start_date, datetime.datetime.now().date())
        except ValueError:
            print("Invalid date format. Please try again.")
            return get_date_range()
    else:
        return (None, None)

def fetch_media_info(cl: Client, hashtag: str, tab_key: str, post_count: int, start_date: Optional[dt.date] = None):
    filename = os.path.join(results_dir, f"{hashtag}_{dt.now().strftime('%Y-%m-%d_%H-%M-%S')}.csv")
    hashtag_info = get_hashtag_info(cl, hashtag)
    with open(filename, 'w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file, delimiter=';')
        writer.writerow(["Hashtag Name", "Hashtag ID", "Total Hits"])
        writer.writerow([hashtag_info["name"], hashtag_info["id"], hashtag_info["media_count"]])
        writer.writerow([])
        writer.writerow(["ID", "Datum en Tijd", "URL", "Media Type", "Like Count", "Comment Count", "Caption Text", "Username", "View Count"])
    max_id = None
    collected_ids: Set[str] = set()
    total_collected = 0
    while True:
        print("Fetching more posts, please wait...")
        batch, new_max_id = cl.hashtag_medias_v1_chunk(hashtag, max_amount=max_amount, tab_key=tab_key, max_id=max_id)
        for media in batch:
            if media.id in collected_ids or (start_date and media.taken_at.date() < start_date):
                continue
            media_info = extract_media_info(media)
            with open(filename, 'a', newline='', encoding='utf-8') as file:
                writer = csv.writer(file, delimiter=';')
                writer.writerow([
                    media_info["id"],
                    media_info["taken_at"],
                    f"https://www.instagram.com/p/{media_info['code']}/",
                    media_info["media_type"],
                    media_info["like_count"],
                    media_info["comment_count"],
                    media_info["caption_text"],
                    media_info["username"],
                    media_info["view_count"]
                ])
            collected_ids.add(media.id)
            total_collected += 1
            if total_collected >= post_count:
                break     
        if not new_max_id or total_collected >= post_count:
            break
        max_id = new_max_id
        time.sleep(random.randint(2, 7))
    print(f"Information for hashtag #{hashtag} has been saved to {filename}.")


    
    

def fetch_all_available_posts(cl, hashtag, start_date=None):
    filename = os.path.join(results_dir, f"{hashtag}_{dt.now().strftime('%Y-%m-%d_%H-%M-%S')}.csv")
    file_exists = os.path.isfile(filename)

    with open(filename, 'a', newline='', encoding='utf-8') as file:
        writer = csv.writer(file, delimiter=';')
        if not file_exists:
            writer.writerow(["ID", "Date and Time", "URL", "Media Type", "Like Count", "Comment Count", "Caption Text", "Username", "View Count"])

    collected_ids = set()

    
    for tab_key in ['recent', 'top']:
        max_id = None
        while True:
            print(f"Fetching more {tab_key} posts, please wait...")
            try:
                batch, new_max_id = cl.hashtag_medias_v1_chunk(hashtag, max_amount=max_amount, tab_key=tab_key, max_id=max_id)
            except instagrapi.exceptions.LoginRequired:
                print("Login required. Please check your session and try again.")
                break

            if not batch:
                print(f"No more {tab_key} posts available. Moving to the next category.")
                break  

            for media in batch:
                if media.id in collected_ids or (start_date and media.taken_at.date() < start_date):
                    continue

                media_info = extract_media_info(media)
                with open(filename, 'a', newline='', encoding='utf-8') as file:
                    writer = csv.writer(file, delimiter=';')
                    writer.writerow([
                        media_info["id"],
                        media_info["taken_at"],
                        f"https://www.instagram.com/p/{media_info['code']}/",
                        media_info["media_type"],
                        media_info["like_count"],
                        media_info["comment_count"],
                        media_info["caption_text"],
                        media_info["username"],
                        media_info["view_count"]
                    ])
                collected_ids.add(media.id)

            if not new_max_id:
                print(f"Completed collecting {tab_key} posts.")
                break  
            max_id = new_max_id
            time.sleep(random.randint(5, 7))
    print(f"Information for hashtag #{hashtag} has been saved to {filename}.")


def load_or_create_hashtag_list() -> Tuple[List[str], str, str, bool]:
    print("1. Track a single hashtag")
    print("2. Track a list of hashtags")
    print("3. Settings")
    choice = input("Choose an option (1, 2 or 3): ").strip()
    success = False
    action = ""

    if choice == '1':
        hashtag_input = input("\nPlease insert the hashtag: ").strip()
        hashtags = [re.sub(r'#', '', hashtag_input).lower()]
        list_name = f"{hashtags[0]}_{datetime.now().strftime('%Y%m%d')}"
        print(f"You've selected: {hashtags[0]}")
        success = True
    elif choice == '2':
        existing_lists = [f for f in os.listdir(settings_dir) if f.endswith('.txt')]
        if not existing_lists:
            print("No existing lists found. Please create a new list.")
            hashtags, list_name = create_new_hashtag_list()
            success = True
        else:
            print("1. Load an existing list of hashtags")
            print("2. Create a new list of hashtags")
            list_choice = input("Choose an option (1 or 2): ").strip()

            if list_choice == '1':
                print("Available lists:")
                for i, filename in enumerate(existing_lists, start=1):
                    print(f"{i}. {filename[:-4]}")
                list_number = int(input("Please select the number of the list you would like to load: ")) - 1
                if 0 <= list_number < len(existing_lists):
                    list_name = existing_lists[list_number][:-4]
                    # Correctly handle the returned values from load_existing_hashtag_list
                    hashtags, list_name, action, success = load_existing_hashtag_list(list_name)
                else:
                    print("Invalid selection.")
                    return [], "", "", False
            elif list_choice == '2':
                hashtags, list_name = create_new_hashtag_list()
                success = True
            else:
                print("Invalid choice. Please try again.")
                return [], "", "", False
    elif choice == '3':  
        settings_menu(None)
        return [], "", "", False                
    else:
        print("Invalid choice. Please try again.")
        return [], "", "", False

    if success:
        print("\nWhat would you like to do?")
        print("1. Collect hashtag statistics")
        print("2. Scrape Hashtag data")
        action_choice = input("Choose an option (1 or 2): ").strip()

        action = "collect_stats" if action_choice == '1' else "scrape_data"
        
        # Shuffle the list of hashtags before returning, if successful
        random.shuffle(hashtags)
    
    return hashtags, list_name, action, success


def create_new_hashtag_list():
    list_name = input("Enter a name for your new list: ").strip()
    hashtags_input = input("Enter hashtags separated by commas: ").strip()
    
    hashtags = [hashtag.strip() for hashtag in hashtags_input.split(',') if hashtag.strip()]
    hashtags = [re.sub(r'#', '', hashtag).lower() for hashtag in hashtags]

    with open(os.path.join(settings_dir, f"{list_name}.txt"), 'w') as file:
        for hashtag in hashtags:
            file.write(f"{hashtag}\n")

    print(f"List created with hashtags: {', '.join(hashtags)}")
    return hashtags, list_name

def load_existing_hashtag_list(list_name) -> Tuple[List[str], str, str, bool]:
    try:
        with open(os.path.join(settings_dir, f"{list_name}.txt"), 'r') as file:
            hashtags = [line.strip() for line in file if line.strip()]
        print("You've selected the following hashtags:")
        for hashtag in hashtags:
            print(hashtag)
        continue_choice = input("Would you like to continue with this list? Yes/No: ").lower()
        if continue_choice != 'yes':
            return [], "", "", False  
        return hashtags, list_name, "action", True  # 'action' needs to be defined or replaced
    except FileNotFoundError:
        print("List not found. Please try again.")
        return [], "", "", False  



def check_files_for_merge(list_name):
    pattern = os.path.join(results_dir, f"{list_name}_*.csv")
    csv_files = [f for f in glob.glob(pattern) if '_merged' not in f]
    return len(csv_files) > 1


def merge_csv_files(prefix):
    
    pattern = os.path.join(results_dir, f"{prefix}*.csv")
    csv_files = [f for f in glob.glob(pattern) if '_merged' not in f]

    if len(csv_files) > 1:
       
        merged_filename = os.path.join(results_dir, f"{prefix}_merged_{datetime.now().strftime('%Y%m%d%H%M%S')}.csv")
        print("Creating new merged file.")

        combined_rows = []
        for file in csv_files:
            with open(file, 'r', newline='', encoding='utf-8') as csvfile:
                reader = csv.reader(csvfile, delimiter=';')
                if file == csv_files[0]:  
                    combined_rows.extend(list(reader))
                else:
                    next(reader) 
                    combined_rows.extend(list(reader))

        with open(merged_filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile, delimiter=';')
            writer.writerows(combined_rows)
        print(f"CSV files merged successfully into: {merged_filename}")
    else:
        print("No multiple CSV files found to merge or only one file matches the prefix.")

def extract_media_info(media) -> Dict:
    return {
        "id": media.id,
        "code": media.code,
        "taken_at": media.taken_at.strftime('%d/%m/%Y %H:%M:%S'),
        "media_type": 'Photo' if media.media_type == 1 else 'Video',
        "like_count": media.like_count,
        "comment_count": media.comment_count,
        "caption_text": media.caption_text if media.caption_text else "",
        "username": media.user.username,
        "view_count": getattr(media, 'view_count', "N/A")
    }

def track_hashtags_and_export_to_csv(cl, hashtags, list_name):
    os.makedirs('results', exist_ok=True)
    csv_filename = f'results/{list_name}_{datetime.now().strftime("%Y%m%d%H%M%S")}.csv'
    
    with open(csv_filename, 'w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file, delimiter=';')
        writer.writerow(['Hashtag ID', 'name', 'Media Count', 'Date and Time'])

    for hashtag in hashtags:
        
        time.sleep(random.randint(3, 7))
        try:
            hashtag_info = get_hashtag_info(cl, hashtag)
            if hashtag_info['id'] is not None:
                with open(csv_filename, 'a', newline='', encoding='utf-8') as file:
                    writer = csv.writer(file, delimiter=';')
                    writer.writerow([hashtag_info['id'], hashtag_info['name'], hashtag_info['media_count'], datetime.now().strftime("%Y-%m-%d %H:%M:%S")])
            else:
                print(f"Hashtag {hashtag} does not exist or is possibly blocked by Instagram.")
                with open(csv_filename, 'a', newline='', encoding='utf-8') as file:
                    writer = csv.writer(file, delimiter=';')
                    writer.writerow(["does not exist", hashtag, "unknown", 0, datetime.now().strftime("%Y-%m-%d %H:%M:%S")])
        except Exception as e:
            print(f"An error occurred while tracking #{hashtag}: {e}")
            with open(csv_filename, 'a', newline='', encoding='utf-8') as file:
                writer = csv.writer(file, delimiter=';')
                writer.writerow(["unknown", hashtag, "unknown", 0, datetime.now().strftime("%Y-%m-%d %H:%M:%S")])

    print(f"CSV successfully saved as: {csv_filename}")

def main():
    cl = login_to_instagram()
    if cl is None:
        print("Login failed. Exiting.")
        return

    continue_search = 'yes'
    while continue_search == 'yes':
        hashtags, list_name, action, success = load_or_create_hashtag_list()
        if not success:
            print("Returning to previous menu...")
            continue  

        if action == "collect_stats":
            track_hashtags_and_export_to_csv(cl, hashtags, list_name)
        elif action == "scrape_data":
            for hashtag in hashtags:
                hashtag_info = get_hashtag_info(cl, hashtag)
                if hashtag_info['media_count'] > 0:
                    search_option, post_count, date_range = get_search_option(hashtag_info['media_count'])
                    start_date, _ = date_range
                    fetch_media_info(cl, hashtag, "recent", post_count, start_date)

                else:
                    print(f"Skipping {hashtag}, as no media count was found.")

        if check_files_for_merge(list_name):
            merge_choice = input("Would you like to merge CSV files for the tracked hashtags? Yes/No: ").strip().lower()
            if merge_choice == 'yes':
                merge_csv_files(list_name)

        continue_search = input("Would you like to do another search? (Yes/No): ").strip().lower()

    cl.dump_settings(os.path.join(settings_dir, "session.json"))
    print("Exiting the script.")

def main_loop():
    main()

if __name__ == "__main__":
    main_loop()



