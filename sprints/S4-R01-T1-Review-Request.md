# S4-R01-T1 Review Request

Send this to Diego, Andres and Eric. It covers the acceptance criterion that the contracts are reviewed with them. Paste their replies into the sign-off table in `S4-R01-T1-Interface-Contracts.md`.

## Message

Hi all, I wrote down the four contracts between recognition, profiles, the controller and the adapter, plus who owns what. Please read `docs/sprint4/S4-R01-T1-Interface-Contracts.md` and answer the question for your area. I have not changed anything in your files.

**Diego**
1. Is the gesture id rule right for your custom and static gestures? Lowercase letters, digits and underscores, starting with a letter, up to 64 characters.
2. Can you pass the set of gesture ids the recognizer emits to `load_profile`? It rejects a binding for an id that never fires.

**Andres**
1. Can the profile UI produce the JSON in Contract B? Version 1, a name, and bindings from gesture id to one of next, previous, pause or resume.
2. Does the UI need to show why a profile was refused? Errors are plain text and list every problem together.

**Eric**
1. Does Contract D match the adapter? Five methods that return true when a key was attempted.
2. Where does enrollment write its result? It should be the profile format above, or something I convert.
3. The `end` command is not bindable by a profile. Any objection?

A short reply is enough. Even "fine as written" works, and I will record it with the date.

Joon

## Reply log

| Person | Reply | Date |
|---|---|---|
| Diego | | |
| Andres | | |
| Eric | | |
