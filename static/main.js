// Object wrapper for reactive variables. cv stands for common variables
var cv = {
  /*
  desiredMelodyMatrix:
//      C4   D4   E4   F4   G4   A4   B4   C5
      [[.00, .50, .50, .00, .00, .00, .00, .00],   //C4
        [.25, .00, .50, .25, .00, .00, .00, .00],   //D4
        [.00, .40, .00, .40, .20, .00, .00, .00],   //E4
        [.00, .00, .40, .00, .40, .20, .00, .00],   //F4
        [.00, .00, .00, .40, .00, .40, .20, .00],   //G4
        [.00, .00, .00, .00, .40, .00, .40, .20],   //A4
        [.00, .00, .00, .00, .30, .50, .00, .20],   //B4
        [.00, .00, .00, .00, .00, .50, .50, .00]], //C5

  desiredHarmonyMatrix:
//      C4   D4   E4   F4   G4   A4   B4   C5
      [[.00, .00, .50, .00, .00, .50, .00, .00],   //C4
        [.00, .00, .00, .50, .00, .00, .50, .00],   //D4
        [.50, .00, .00, .00, .50, .00, .00, .00],   //E4
        [.00, .50, .00, .00, .00, .50, .00, .00],   //F4
        [.00, .00, .50, .00, .00, .00, .50, .00],   //G4
        [.00, .00, .00, .50, .00, .00, .00, .50],   //A4
        [.00, .50, .00, .00, .50, .00, .00, .00],   //B4
        [.00, .00, .50, .00, .00, .50, .00, .00]], //C5
  */

  desiredMelodicPermutationMatrix:
//      C4   D4   E4   F4   G4   A4   B4   C5
      [[.00, 1.0, .00, .00, .00, .00, .00, .00], //C4
        [.00, .00, 1.0, .00, .00, .00, .00, .00], //D4
        [.00, .00, .00, 1.0, .00, .00, .00, .00], //E4
        [.00, .00, .00, .00, 1.0, .00, .00, .00], //F4
        [.00, .00, .00, .00, .00, 1.0, .00, .00], //G4
        [.00, .00, .00, .00, .00, .00, 1.0, .00], //A4
        [.00, .00, .00, .00, .00, .00, .00, 1.0], //B4
        [1.0, .00, .00, .00, .00, .00, .00, .00]], //C5

  desiredHarmonicPermutationMatrix:
//      C4   D4   E4   F4   G4   A4   B4   C5
      [[.00, .00, 1.0, .00, .00, .00, .00, .00], //C4
        [.00, .00, .00, 1.0, .00, .00, .00, .00], //D4
        [.00, .00, .00, .00, 1.0, .00, .00, .00], //E4
        [.00, .00, .00, .00, .00, 1.0, .00, .00], //F4
        [.00, .00, .00, .00, .00, .00, 1.0, .00], //G4
        [.00, .00, .00, .00, .00, .00, .00, 1.0], //A4
        [.00, 1.0, .00, .00, .00, .00, .00, .00], //B4
        [1.0, .00, .00, .00, .00, .00, .00, .00]], //C5

  equalMelodyMatrix:
//      C4    D4    E4    F4    G4    A4    B4    C5
      [[.125, .125, .125, .125, .125, .125, .125, .125],   //C4
        [.125, .125, .125, .125, .125, .125, .125, .125],   //D4
        [.125, .125, .125, .125, .125, .125, .125, .125],   //E4
        [.125, .125, .125, .125, .125, .125, .125, .125],   //F4
        [.125, .125, .125, .125, .125, .125, .125, .125],   //G4
        [.125, .125, .125, .125, .125, .125, .125, .125],   //A4
        [.125, .125, .125, .125, .125, .125, .125, .125],   //B4
        [.125, .125, .125, .125, .125, .125, .125, .125]], //C5

  equalHarmonyMatrix:
//      C4    D4    E4    F4    G4    A4    B4    C5
      [[.125, .125, .125, .125, .125, .125, .125, .125],   //C4
        [.125, .125, .125, .125, .125, .125, .125, .125],   //D4
        [.125, .125, .125, .125, .125, .125, .125, .125],   //E4
        [.125, .125, .125, .125, .125, .125, .125, .125],   //F4
        [.125, .125, .125, .125, .125, .125, .125, .125],   //G4
        [.125, .125, .125, .125, .125, .125, .125, .125],   //A4
        [.125, .125, .125, .125, .125, .125, .125, .125],   //B4
        [.125, .125, .125, .125, .125, .125, .125, .125]] //C5

}

