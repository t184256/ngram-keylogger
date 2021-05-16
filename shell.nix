{ pkgs ? import <nixpkgs> { } }:
with pkgs;
mkShell {
  buildInputs = [
    sqlite-interactive
    (python3.withPackages (ps: with ps; [
      click
      evdev
      psutil
      pyxdg
    ]))
  ];
}
