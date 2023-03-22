import database
from models import bayesucb
import spotipy


def main():
    user = database.User(client_id='d3e0dfeb24424090bf02738a8954b759', client_secret='412c10abb6424d5cb389ef3a85344d50',
                         connxn_string='mongodb://127.0.0.1:27017/')

    # adding random songs and their ratings for training

    dancing_with_ghosts = '1TQXIltqoZ5XXyfCbAeSQQ'
    only = '5lehoWkVPujeOAwb8BO0uK'
    wtf = '7mYrw8DN9vDg1c5qqpDboC'
    illwait = '6Q3K9gVUZRMZqZKrXovbM2'
    unme = '2umqe74ItZBWCdChsHtXjQ'
    adult = '4AOPgMrdBlaLFF5dxzIhdx'
    lamborghini = '6JyuJFedEvPmdWQW0PkbGJ'
    majesty = '08E0TIudwefGjA27W4zrnf'
    dieaking = '1s70cjkrdj9lpEeQQlmS9l'
    deathwaltz = '7LUsIrW9BlMJs3WhXne9Ue'

    user.add_song(dancing_with_ghosts)
    user.add_song(only)
    user.add_song(wtf)
    user.add_song(illwait)
    user.add_song(unme)
    user.add_song(adult)
    user.add_song(lamborghini)
    user.add_song(majesty)
    user.add_song(dieaking)
    user.add_song(deathwaltz)

    user.add_rating(dancing_with_ghosts, 3)
    user.add_rating(only, 5)
    user.add_rating(wtf, 1)
    user.add_rating(illwait, 4)
    user.add_rating(unme, 3)
    user.add_rating(adult, 2)
    user.add_rating(lamborghini, 8)
    user.add_rating(majesty, 9)
    user.add_rating(dieaking, 9)
    user.add_rating(deathwaltz, 10)

    # Train RL model and store weights for user
    trainer = bayesucb.BayesUCBTrainer(user)
    trainer.train()

    sp = spotipy.Spotify(auth_manager=spotipy.SpotifyClientCredentials(client_id='d3e0dfeb24424090bf02738a8954b759',
                                                                       client_secret='412c10abb6424d5cb389ef3a85344d50'))

    predictor = bayesucb.BayesUCBPredictor(user, sp)
    print(predictor.recommend())


if __name__ == "__main__":
    main()
