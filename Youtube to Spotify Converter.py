import tkinter as tk
from tkinter import messagebox
from tkinter import ttk
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import youtube_dl
import threading
import ctypes

def center_window(window):
        window.update_idletasks()
        width = window.winfo_width()
        height = window.winfo_height()
        x = (window.winfo_screenwidth() // 2) - (width // 2)
        y = (window.winfo_screenheight() // 2) - (height // 2)
        window.geometry('{}x{}+{}+{}'.format(width, height, x, y))
def cancel_conversion():
    global cancel_conversion_flag
    cancel_conversion_flag = True

def authenticate_and_convert():
    url = url_entry.get()
    playlist_name = playlist_name_entry.get()

    # Create a progress bar window
    progress_window = tk.Toplevel(window)
    progress_window.title("Progress")
    progress_window.geometry("300x150")
    progress_window.resizable(False, False)
    progress_window.iconbitmap("icon.ico")
    progress_window.protocol("WM_DELETE_WINDOW", cancel_conversion)

    # Center progress window on the screen
    progress_window.update_idletasks()
    width = progress_window.winfo_width()
    height = progress_window.winfo_height()
    x = (progress_window.winfo_screenwidth() // 2) - (width // 2)
    y = (progress_window.winfo_screenheight() // 2) - (height // 2)
    progress_window.geometry('{}x{}+{}+{}'.format(width, height, x, y))

    progress_label = tk.Label(progress_window, text="Creating Spotify playlist...", font=("Helvetica", 12))
    progress_label.pack(pady=20)
    progress_bar = ttk.Progressbar(progress_window, length=200, mode='determinate')
    progress_bar.pack(pady=10)
    cancel_button = tk.Button(progress_window, text="Cancel", command=cancel_conversion)
    cancel_button.pack(pady=10)

    # Authenticate with Spotify
    sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id='c07970e9043841ad81d0d653f167eb71',
                                                   client_secret='1315f268abff4589990d6cbf2c003e0e',
                                                   redirect_uri='http://localhost:8888/callback',
                                                   scope='playlist-modify-private'))

    def create_playlist():
        try:
            # Extract YouTube playlist info (only the names)
            ydl_opts = {'extract_flat': 'in_playlist', 'skip_download': True, 'ignoreerrors': True, 'forcejson': True}
            with youtube_dl.YoutubeDL(ydl_opts) as ydl:
                playlist_info = ydl.extract_info(url, download=False)
                videos = playlist_info['entries']

                # Get current Spotify user's profile
                user_profile = sp.current_user()

                # Create a new Spotify playlist
                sp_playlist = sp.user_playlist_create(user=user_profile['id'],
                                                      name=playlist_name,
                                                      public=False,
                                                      description='Converted from YouTube')
                spotify_playlist_id = sp_playlist['id']

                # Calculate progress bar increment
                increment = 100 / len(videos)

                # Add videos to the Spotify playlist
                not_found_songs = []
                not_added_songs = []

                for index, video in enumerate(videos):
                    if cancel_conversion_flag:
                        # Cancel button was pressed
                        progress_window.destroy()
                        delete_playlist(sp, spotify_playlist_id)
                        messagebox.showinfo("Conversion Canceled", "Playlist creation was canceled.")
                        return

                    video_title = video['title']
                    query = video_title
                    search_results = sp.search(q=query, type='track', limit=1)
                    if len(search_results['tracks']['items']) > 0:
                        track_uri = search_results['tracks']['items'][0]['uri']
                        try:
                            sp.playlist_add_items(playlist_id=spotify_playlist_id, items=[track_uri])
                        except:
                            not_added_songs.append(video_title)
                    else:
                        not_found_songs.append(video_title)

                    # Update progress bar
                    progress_bar['value'] = (index + 1) * increment
                    progress_window.update()

                # Close progress window
                progress_window.destroy()

                # Show success message and option to create another playlist
                message = "Playlist successfully created!\n\n"

                if len(not_found_songs) > 0:
                    message += "Songs not found on Spotify:\n"
                    message += "\n".join(not_found_songs)
                    message += "\n\n"

                if len(not_added_songs) > 0:
                    message += "Songs not added to playlist:\n"
                    message += "\n".join(not_added_songs)

                message += "\n\nCreated by LoneLee with ChatGPT's Help"

                result = messagebox.askquestion("Conversion Complete", message + "\nCreate another playlist?")
                if result == 'yes':
                    url_entry.delete(0, tk.END)
                    playlist_name_entry.delete(0, tk.END)
                else:
                    window.quit()

        except Exception as e:
            # Delete the playlist and display error message
            delete_playlist(sp, spotify_playlist_id)
            progress_window.destroy()
            messagebox.showerror("Error", f"An error occurred:\n{str(e)}")

    def delete_playlist(spotify_client, playlist_id):
        spotify_client.current_user_unfollow_playlist(playlist_id)



    # Start playlist creation in a separate thread
    global cancel_conversion_flag
    cancel_conversion_flag = False
    thread = threading.Thread(target=create_playlist)
    thread.start()

# Create the GUI window
window = tk.Tk()
window.title("YouTube to Spotify Playlist Converter")
window.iconbitmap("icon.ico")

# Center the window on the screen
center_window(window)

# Create URL entry field
url_label = tk.Label(window, text="YouTube Playlist URL:")
url_label.pack(pady=10)
url_entry = tk.Entry(window, width=50)
url_entry.pack(pady=5)

# Create playlist name entry field
playlist_name_label = tk.Label(window, text="Spotify Playlist Name:")
playlist_name_label.pack(pady=10)
playlist_name_entry = tk.Entry(window, width=50)
playlist_name_entry.pack(pady=5)

# Create convert button
convert_button = tk.Button(window, text="Convert", command=authenticate_and_convert)
convert_button.pack(pady=10)

# Attribution label
attribution_label = tk.Label(window, text="Created by LoneLee with ChatGPT's Help", font=("Helvetica", 8))
attribution_label.pack(side="bottom", pady=10)

# Start the GUI event loop
window.mainloop()
