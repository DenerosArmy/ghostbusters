Phone to server message format

```
{
  action: "compass" or "ghost"
  args: [x (latitude), y (longitude), horizontal accuracy (meters), heading (degrees 0-360)]
}
```

Server to phone message format

```
{
  action: "compass"
  args: [prob 0-90, prob 90-180, prob 180-270, prob 270-360]
}
```
Probabilities are decimals in the range 0.0-1.0

```
{
  action: "ghost"
  location: [x (latitude), y (longitude)] OR null
}
```
