{
  description = "ngram-keylogger: secure typing stats";

  inputs.flake-utils.url = "github:numtide/flake-utils";
  inputs.nixpkgs.url = "github:NixOS/nixpkgs";

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem
      (system:
        let pkgs = nixpkgs.legacyPackages.${system}; in
        rec {
          ngram-keylogger = pkgs.python3Packages.buildPythonPackage {
            pname = "ngram-keylogger: typing stats that don't leak passwords";
            version = "0.0.1";
            src = ./.;
            propagatedBuildInputs = with pkgs; [
              python3Packages.click
              python3Packages.evdev
            ];
          };
          defaultPackage = ngram-keylogger;
          devShell = import ./shell.nix { inherit pkgs; };
        }
      );
}
