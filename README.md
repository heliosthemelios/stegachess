# Stegachess

Stegachess is a python CLI which allow you to encode data inside of a chess game. For example, the following game :

```
1. h4 c5 2. a3 f5 3. g4 b6 4. Bg2 Na6 5. c4 h5 6. Qa4 Kf7 7. Bc6 fxg4 8. Qb3 Rb8 9. a4 Bb7 10. Rh3 Nb4 11. d4 Na2 12. Kd1 Qe8 13. Qf3+ Ke6 14. Ke1 Ba6 15. Rg3 Rh6 16. Rg2 Qd8 17. a5 Rh8 18. Qxf8 Bb5 19. Qxd8 Rh6 20. Kf1 cxd4 21. Nc3 Kd6 22. Bd2 *
```

Means "Steganography is awesome !"

It is fully compatible with [James Stanley's version](https://incoherency.co.uk/blog/stories/chess-steg.html), but with more features

# Features

### Use stockfish to remove stupid moves

You can use stockfish (or any game engine you like) to prevent blunders. You can also tweak it with a few options, making your secrets even harder to be found !

### Start from a specific position
It is possible to start the encoding from a specific position, which is fun, and can be an awesome idea for a CTF !

### Compressed mode
A mode which tries to limit the number of moves to store your data. It filter moves that reduce enthropy to only have move that create positions with a lot of possibility (which result in more data stored in less moves). In average from my tests, this mode reduces the number of moves by 30%.