import toml


__all__ = ['config']

config = toml.load('./config.toml')
