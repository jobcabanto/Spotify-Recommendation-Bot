# Spotify Playlist Recommendation Bot

The goal of the project was to quantify my musical taste and understand my listening patterns from a numerical point of view. The recommendation model analyzes songs based on Spotify's "Danceability", "Energy", and "Acousticness" features.

Tools/Technologies Used:
- Python
- Spotify API
- Scikit-Learn
- Pandas
- Matplotlib

Project Summary:
- Dataset is comprised of 100 songs from my current music rotation (good_songs) and 100 songs I do not listen to daily (bad_songs)
- Model features were reduced from Spotify's 13 quantitative audio features to 3 (Danceability, Energy, and Acousticness) using dimensionality reduction techniques
- The specific algorithm used for the project was the K-Nearest Neighbours algorithm with KD-trees
- Using the cross-validation with the elbow method, 8 neighbours were the best-suited amount of neighbours for the model
- After applying the model to a test set, the model performed with 86% accuracy. 

![alt text](https://github.com/jobcabanto/Spotify-Recommendation-Bot/blob/main/res/Figure_1.png)
