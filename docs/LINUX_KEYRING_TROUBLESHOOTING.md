# Guia de Solução de Problemas do Keyring no Linux

Este guia ajuda a resolver problemas relacionados ao keyring no SafeStic em sistemas Linux.

## 🔍 Problemas Comuns

### 1. Erro "No module named 'keyring'"

**Solução:** Execute o script de setup que instala automaticamente as dependências:

```bash
# Para sistemas baseados em Debian/Ubuntu
sudo apt update
sudo apt install python3-dev libdbus-glib-1-dev gnome-keyring pkg-config cmake build-essential libdbus-1-dev

# Para sistemas baseados em Fedora/CentOS/RHEL
sudo dnf install python3-devel dbus-glib-devel gnome-keyring pkgconf cmake gcc-c++ dbus-devel

# Para Arch/Manjaro
sudo pacman -S python-devel dbus-glib gnome-keyring pkgconf cmake base-devel dbus

# Para openSUSE
sudo zypper install python3-devel dbus-1-glib-devel gnome-keyring pkg-config cmake gcc-c++ dbus-1-devel
```

### 2. Erro "No recommended backend was available"

**Causa:** O keyring não encontrou um backend adequado para armazenar credenciais.

**Soluções:**

#### Opção A: Inicializar GNOME Keyring
```bash
# Inicializar o daemon do gnome-keyring
gnome-keyring-daemon --start --components=secrets

# Ou adicionar ao seu .bashrc/.zshrc
echo 'eval $(gnome-keyring-daemon --start --components=secrets)' >> ~/.bashrc
```

#### Opção B: Usar arquivo .env (Recomendado para servidores)
```bash
# Copiar o arquivo de exemplo
cp .env.example .env

# Editar com suas credenciais
nano .env
```

### 3. Erro de compilação do dbus-python

**Erro típico:**
```
dbus-gmain| Did not find pkg-config by name 'pkg-config'
dbus-gmain| Found pkg-config: NO
```

**Solução:** O script de setup agora instala automaticamente as dependências de build necessárias. Se ainda houver problemas:

```bash
# Instalar dependências de build manualmente
sudo apt install pkg-config cmake build-essential libdbus-1-dev  # Ubuntu/Debian
sudo dnf install pkgconf cmake gcc-c++ dbus-devel              # Fedora/CentOS
sudo pacman -S pkgconf cmake base-devel dbus                   # Arch/Manjaro
sudo zypper install pkg-config cmake gcc-c++ dbus-1-devel     # openSUSE
```

## 🧪 Testando a Instalação

### Teste Rápido
```bash
# Executar teste básico
python tests/test_keyring_fix.py

# Executar teste específico para Linux
python test_linux_keyring.py

# Verificar se o sistema está funcionando
make check
```

### Verificação Manual do Keyring
```python
# Testar keyring manualmente
python3 -c "
import keyring
print(f'Backend: {keyring.get_keyring()}')
try:
    keyring.set_password('test', 'user', 'pass')
    print('✅ Keyring funcionando')
except Exception as e:
    print(f'❌ Erro: {e}')
"
```

## 🔧 Alternativas e Fallbacks

### 1. Usar keyrings.alt
Se o dbus-python falhar, o sistema automaticamente tenta instalar `keyrings.alt`:

```bash
pip install keyrings.alt
```

### 2. Configurar backend específico
```python
# No seu código Python
import keyring
from keyrings.alt.file import PlaintextKeyring

# Usar backend de arquivo (menos seguro, mas funcional)
keyring.set_keyring(PlaintextKeyring())
```

### 3. Usar apenas arquivo .env
```bash
# Configurar para usar apenas .env
export SAFESTIC_CREDENTIAL_SOURCE=env
```

## 🐧 Configurações Específicas por Distribuição

### Ubuntu/Debian
```bash
# Instalar GNOME Keyring e dependências
sudo apt install gnome-keyring libsecret-1-0 libsecret-1-dev

# Para ambientes sem GUI
sudo apt install dbus-x11
export $(dbus-launch)
```

### Fedora/CentOS/RHEL
```bash
# Instalar GNOME Keyring
sudo dnf install gnome-keyring libsecret-devel

# Inicializar D-Bus se necessário
sudo systemctl start dbus
```

### Arch/Manjaro
```bash
# Instalar GNOME Keyring
sudo pacman -S gnome-keyring libsecret

# Adicionar ao .xinitrc se usar X11
echo 'eval $(gnome-keyring-daemon --start --components=secrets)' >> ~/.xinitrc
```

### Servidores (sem GUI)
```bash
# Para servidores, recomenda-se usar arquivo .env
echo "SAFESTIC_CREDENTIAL_SOURCE=env" >> ~/.bashrc

# Ou usar keyring com backend de arquivo
pip install keyrings.alt
export PYTHON_KEYRING_BACKEND=keyrings.alt.file.PlaintextKeyring
```

## 🔒 Considerações de Segurança

### Keyring vs .env
- **Keyring:** Mais seguro, credenciais criptografadas
- **.env:** Menos seguro, mas mais compatível

### Recomendações
1. **Desktop:** Use keyring com GNOME Keyring
2. **Servidor:** Use arquivo .env com permissões restritas
3. **CI/CD:** Use variáveis de ambiente do sistema

```bash
# Definir permissões seguras para .env
chmod 600 .env
chown $USER:$USER .env
```

## 📋 Checklist de Solução de Problemas

- [ ] Dependências de sistema instaladas
- [ ] Python 3.8+ instalado
- [ ] Ambiente virtual ativo
- [ ] Dependências Python instaladas
- [ ] GNOME Keyring inicializado (se aplicável)
- [ ] Arquivo .env configurado (fallback)
- [ ] Testes passando
- [ ] `make check` funcionando

## 🆘 Suporte

Se os problemas persistirem:

1. Execute `python test_linux_keyring.py` e compartilhe a saída
2. Verifique os logs em `/tmp/safestic.log`
3. Teste com `SAFESTIC_CREDENTIAL_SOURCE=env make check`

## 📚 Recursos Adicionais

- [Documentação oficial do keyring](https://pypi.org/project/keyring/)
- [GNOME Keyring Documentation](https://wiki.gnome.org/Projects/GnomeKeyring)
- [keyrings.alt Backends](https://pypi.org/project/keyrings.alt/)