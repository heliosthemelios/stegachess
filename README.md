# Stegachess

Stegachess est une interface en ligne de commande Python qui vous permet d'encoder des données à l'intérieur d'une partie d'échecs. Par exemple, la partie suivante :

```
1. h4 c5 2. a3 f5 3. g4 b6 4. Bg2 Na6 5. c4 h5 6. Qa4 Kf7 7. Bc6 fxg4 8. Qb3 Rb8 9. a4 Bb7 10. Rh3 Nb4 11. d4 Na2 12. Kd1 Qe8 13. Qf3+ Ke6 14. Ke1 Ba6 15. Rg3 Rh6 16. Rg2 Qd8 17. a5 Rh8 18. Qxf8 Bb5 19. Qxd8 Rh6 20. Kf1 cxd4 21. Nc3 Kd6 22. Bd2 *
```

Signifie "Steganography is awesome !"

Il est entièrement compatible avec [la version de James Stanley](https://incoherency.co.uk/blog/stories/chess-steg.html), mais avec plus de fonctionnalités

# Fonctionnalités

### Utiliser stockfish pour supprimer les coups stupides

Vous pouvez utiliser stockfish (ou n'importe quel moteur d'échecs que vous aimez) pour éviter les bévues. Vous pouvez également l'ajuster avec quelques options, rendant vos secrets encore plus difficiles à trouver !

### Commencer depuis une position spécifique
Il est possible de commencer l'encodage à partir d'une position spécifique, ce qui est amusant et peut être une excellente idée pour un CTF !

### Mode compressé
Un mode qui essaie de limiter le nombre de coups pour stocker vos données. Il filtre les coups qui réduisent l'entropie pour ne garder que les coups qui créent des positions avec beaucoup de possibilités (ce qui permet de stocker plus de données en moins de coups). En moyenne d'après mes tests, ce mode réduit le nombre de coups de 30%.