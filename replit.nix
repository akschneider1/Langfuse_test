{ pkgs }: {
  deps = [
    pkgs.docker-compose
    pkgs.python311
    pkgs.python311Packages.pip
    pkgs.wget
    pkgs.curl
    pkgs.jq
  ];
}
