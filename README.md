# CreateVC Core releases

Public binary distribution for CreateVC Core (NeoForge **1.21.1**).
Source code and private build history are not published here.

## Packwiz

Run once from your pack directory:

```sh
packwiz github add Jammersmurph/CreateVC-Core-Releases --regex '^CreateVC-Core\.jar$'
```

To pick up new builds:

```sh
packwiz update --all
```

Commit/publish the changed `.pw.toml`, `index.toml` and `pack.toml` files in your
pack. Packwiz Installer follows those files; it does not independently update
mods just because a new GitHub release exists.

Each successful private build pushes a **new immutable tag**, for example
`v1.1.0-build.42.1`. This repository's workflow verifies the binary and publishes
a GitHub release with `CreateVC-Core.jar`, its SHA-256 checksum and build metadata.
The newest build is marked **Latest**. Published assets are never replaced.
R2 is not part of this publishing path.

The default branch contains only publishing automation and this documentation.
Binary files live in tagged commits and release assets. The repository-scoped
deploy key used by the private builder has no access to other repositories;
release creation uses this repository's own Actions token.

## Essentials permissions

Essentials runs on the logical server (dedicated or integrated), with vanilla
menu types and optional LuckPerms integration. Existing Core/modpack client
requirements remain unchanged.

Example console commands:

```text
lp group default permission set createvc.essentials.home true
lp group default meta set createvc.essentials.homes 3
lp group vip parent add default
lp group vip meta set createvc.essentials.homes 10
lp group vip meta set createvc.essentials.teleport.cooldown 10
lp group vip meta set createvc.essentials.teleport.warmup 1
```

Grant individual capabilities, not `createvc.essentials.*`, to normal players.
Administrative actions, access to other players' data and teleport/limit bypasses
have separate nodes. Config: `config/createvc-essentials.json`.
