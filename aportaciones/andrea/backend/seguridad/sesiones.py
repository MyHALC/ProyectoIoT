import hashlib
import secrets
import time
from redis.exceptions import WatchError
from config import config
from db.redis import session_repository as modulo_sesiones
from db.redis.connection import redis_client
from seguridad.cifrado import ProtectorLlaves, contexto_sesion
from seguridad.protocolo import Protocolo


class RepositorioSesiones:
    def __init__(self, cache=None):
        self.cache = cache if cache is not None else redis_client  #self.cache es el cliente de Python para enviar comandos a   Redis
        self.epoca_clave = config.prefijo + 'epoca'       #epoca es la generación de seguridad de Redis, config.prefijo es el comienzo de nombre condigurado en el .env,
                                                            #toma el valor del entorno (iot2), se usa para reconocer la generación de redis

    @staticmethod                               #metodo que no necesita self
    def clave(id_sesion):    #recibe el ID que conoce el cliente y permite calcular donde se guarda su sesión
        return modulo_sesiones._clave(id_sesion)  #llama a _clave del modulo de BD para que escritura, lectura y borrado calculen el mismo nombre de sesion (SHA-265 del ID)

    @staticmethod
    def indice(entidad):   #entidad reune tipo, ID pub y priv de la identidad de SQL, se necesita para saber a quien pertenece la sesion
        return f'{config.prefijo}cliente:{entidad.tipo}:{entidad.id_priv}' #agrupa claves aux del proyecto, permite localizar la sesion para revocarla o reemplazarla

    def epoca(self):   #obtiene la generacion de seguridad de Redis
        #Identifica el arranque actual de Redis para rechazar paquetes anteriores
        prefijo_arranque = self.cache.info('server')['run_id'] + ':'    #run_id identifica el proceso Redis actual
        nueva_epoca = prefijo_arranque + secrets.token_hex(16)             #se generan 16 bytes aleatorios, permite cambiar la generacion si se perdio la clave de epoca durante el arranque
        #este script lee la epoca guardada con GET, se pertenece al mismo arranque de Redis, la devuelve, si no, guarda y devuelve la nueva
        script = """
            local vieja=redis.call('GET',KEYS[1]);
            if vieja and string.sub(vieja,1,string.len(ARGV[1]))==ARGV[1] then return vieja end;
            redis.call('SET',KEYS[1],ARGV[2]); return ARGV[2];
        """
        return self.cache.eval(script, 1, self.epoca_clave, prefijo_arranque, nueva_epoca) #EVAL ejecuta LUA dentro de Redis, 1 es cuantos argumentos son KEYS, los demas son ARGS

    def emitir_reto(self, entidad):  #crea el reto pendiente para una identidad ya comprobada por la autenticación
    #Guarda el reto pendiente con su caducidad
        epoca = self.epoca()    #obtiene la generacion con la que estara ligado el reto
        reto = {      #empieza el diccionario
            'reto_id': secrets.token_hex(24),    #distingue cada reto pendiente
            'nonce': secrets.token_hex(32),      #valor de uso unico, hace diferente cada intercambio de reto
            'id_cliente': entidad.id_pub, #id pub que se comparte con el cliente, liga el reto a la identidad sin exponer el id interno de MariaDB
            'tipo': entidad.tipo,
            'servidor': config.servidor,
            'epoca': epoca,
            'huella': hashlib.sha256(entidad.llave.encode('ascii')).hexdigest(),  #resumen SHA-256 del texto de la llave de identidad guardada y protegida
            'expira': int(time.time()) + config.reto_ttl, #limita el tiempo
        }
        clave = config.prefijo + 'reto:' + reto['reto_id']
        self.cache.set(clave, Protocolo.json(reto).decode(), ex=config.reto_ttl) #SET guarda el diccionario convertido a JSON, 'ex' asigna segundos para que el reto expire
        return reto

    def consumir_reto(self, reto):
       #Comprueba y elimina el reto en una sola operación de Redis.
        if reto['epoca'] != self.epoca(): #compara la generacion del reto con la actual
            return False  #rechaza un reto emitido en otra generacion
        if reto['expira'] <= time.time(): #compara la fecha limite con el reloj del backend
            return False #rechaza reto si esta vencido
        clave = config.prefijo + 'reto:' + reto['reto_id']
       #script de lua, revalida dentro de Redis la generacion e igualdad exacta del JSON almacenado, cualquier dif. devuelve 0
        script = """     
            if redis.call('GET',KEYS[2])~=ARGV[2] or redis.call('GET',KEYS[1])~=ARGV[1] then return 0 end;  
            return redis.call('DEL',KEYS[1]);
        """
        contenido = Protocolo.json(reto).decode()
        resultado = self.cache.eval(script, 2, clave, self.epoca_clave, contenido, reto['epoca'])
        return bool(resultado)   #convierte el resultado numerico en True o false

    def reservar_hmac(self, entidad, nonce, epoca):
        #Acepta el nonce una sola vez y conserva su marca con vencimiento.
        if self.epoca() != epoca:
            return False
        clave = f'{config.prefijo}hmac:{entidad.tipo}:{entidad.id_priv}:{nonce}' #construye una marma HMAC con prefijo, tipo, ID privado y nonce, asi detecta que entidad ya uso ese valor una vez
        script = """
            if redis.call('GET',KEYS[1])~=ARGV[1] then return 0 end;
            return redis.call('SET',KEYS[2],'1','EX',ARGV[2],'NX') and 1 or 0;
        """
        duracion_marca = config.hmac_ttl * 2 + 1
        resultado = self.cache.eval(script, 2, self.epoca_clave, clave, epoca, duracion_marca) #ejecuta la comprobacion de generacion y reserva como una sola operacion en Redis
        return bool(resultado)

    def crear(self, entidad, llave_identidad):  #recibe la identidad autenticada y los bytes de su llave de identidad
        #Prepara una llave nueva y guarda una única sesión para esta entidad.
        id_sesion = secrets.token_urlsafe(32)  #referencia que viaja fuera del cifrado para buscar la sesion
        indice = self.indice(entidad)    #calcula el indice de sesion
        llave_sesion = secrets.token_bytes(32)
        expira = int(time.time()) + config.ttl
        epoca = self.epoca()

        protector = ProtectorLlaves(config.maestra)  #encapsula AES-GCM con la mestra del backend
        llave_protegida = protector.proteger(llave_sesion, contexto_sesion(id_sesion))   #contiene el ID de esta sesion y se autemtica con AES-GCM
        registro = {   #registro de seguridad que es incorporara al hash de Redis
            'tipo': entidad.tipo,
            'id_cliente': entidad.id_pub,
            'id_priv': entidad.id_priv,
            'expira': expira,
            'epoca': epoca,
            'indice': indice,
            'prefijo': config.prefijo,
            'huella': hashlib.sha256(llave_identidad).hexdigest(),
            'llave_sesion': llave_protegida, #guarda la llave de sesion cifrada con la maetsra
        }
        self._guardar_sesion(entidad, id_sesion, registro)

        return {  #construye el resultado logico de apertura de sesion
            'id_sesion': id_sesion,
            'id_cliente': entidad.id_pub,
            'tipo': entidad.tipo,
            'llave_sesion': Protocolo.base64(llave_sesion),
            'expira': expira,
            'proposito': 'inicio-sesion',   #etiqueta la respuesta
            'servidor': config.servidor, #identifica el servidor que abrio la sesion
        }

    def _guardar_sesion(self, entidad, id_sesion, registro):  #publica la sesion y sustituye la sesion la anterior de esa identidad
        #Reemplaza la anterior y publica la nueva dentro de la misma transacción.
        clave = self.clave(id_sesion)   #calcula session:<hash> para el nuevo ID
        indice = registro['indice']   #recupera el indice que debe apuntar a esta sesion
        epoca = registro['epoca']
        # WATCH detecta otro login simultáneo; se reintenta sin publicar dos sesiones.
        for _ in range(12):   #los 12 intentos ponen limite al reintento por logins simultaneos
            with self.cache.pipeline() as transaccion:  #un pipeline agrupa comandos Redis
                try:
                    transaccion.watch(indice, self.epoca_clave)   #watch vigila indice y epoca, si otro login o cambio de generacion los modifica, EXEC aborta
                    if transaccion.get(self.epoca_clave) != epoca:
                        raise RuntimeError('Redis reinició durante el inicio de sesión.')  #interrumpe el login
                    anterior = transaccion.get(indice)  #permite retirar solo la sesion de esa identidad al reemplazarla
                    transaccion.multi() #inicia la cola
                    if anterior: #comprueba si habia una sesion que reemplazar
                        transaccion.delete(anterior, anterior + ':repeticiones')  #encola el borrado del HASH anterior y su conjunto de peticiones
                    modulo_sesiones.crear_sesion(   #llama a crear sesion del modulo de Redis
                        entidad.tipo, entidad.id_pub, campos=registro,
                        ttl=config.ttl, session_id=id_sesion, pipeline=transaccion,
                    )
                    transaccion.set(indice, clave, ex=config.ttl)  #set liga la identidad con su nuevo hash
                    transaccion.execute()   #EXEC confrima los comandos si WATCH sigue valido
                    return   #sale del metodo cuando se publica la sesion
                except WatchError:  #avisa que cambio una clave vigilada
                    continue
        raise RuntimeError('No se pudo reservar la sesión.')   #falla despues de agotar los doce intentos

    def obtener(self, id_sesion):  #lee una sesion
        #Recupera la sesión solo si todas sus referencias siguen vigentes.
        epoca = self.epoca()
        registro = modulo_sesiones.obtener_sesion(id_sesion)  #llama al modulo Redis para leer el hash y verificar su TTL y campos
        if not registro:
            return None
        if registro.get('prefijo') != config.prefijo:
            return None
        if registro.get('epoca') != epoca:
            return None
        if int(registro['expira']) <= time.time():
            return None
        if registro['tipo_cuenta'] != registro['tipo']:
            return None
        if registro['id_pub'] != int(registro['id_cliente']):
            return None
        if self.cache.get(registro['indice']) != self.clave(id_sesion):
            return None
        return registro

    def consumir_peticion(self, id_sesion, peticion_id, epoca):  #identificador de peticion
        #Devuelve 1 si es nueva, 0 si se repite y -1 si la sesión vencio
        clave = self.clave(id_sesion)   #calcula el hash de sesion al que se vinculara la marca
        # EVAL comprueba y registra sin que otra petición se interponga.
        #SADD añade el ID  a un conjunto, devuelve 1 si lo añadio y 0 si ya estaba, esto distingue un paquete nuevo de una copia
        script = """
            local ttl=redis.call('TTL',KEYS[1]);
            if ttl<=0 or redis.call('GET',KEYS[3])~=ARGV[2] then return -1 end;
            if redis.call('SADD',KEYS[2],ARGV[1])==0 then return 0 end;
            redis.call('EXPIRE',KEYS[2],ttl); return 1;
        """
        resultado = self.cache.eval(script, 3, clave, clave + ':repeticiones',
                                    self.epoca_clave, peticion_id, epoca)
        return int(resultado)

    def eliminar_clave(self, clave, indice):
        #Retira la sesión sin borrar un índice que ya pertenece a otra nueva.
        #Borra el hash de esa sesion
        #Solo limpia la referencia si aun pertenece a la sesion que esta cerrando
        script = """
            redis.call('DEL',KEYS[1],KEYS[2]);
            if redis.call('GET',KEYS[3])==KEYS[1] then redis.call('DEL',KEYS[3]) end;
        """
        self.cache.eval(script, 3, clave, clave + ':repeticiones', indice)

    def cerrar(self, id_sesion, registro):
        #Cierre solicitado por el cliente.
        self.eliminar_clave(self.clave(id_sesion), registro['indice'])  #traduce el ID a su hash y delega la limpieza del hash, marcas e indice

    def invalidar(self, entidad):  #Retira la sesión cuando se revoca
        indice = self.indice(entidad)   #calcula el indice de la identidad afectada
        clave = self.cache.get(indice) #lee el nombre del hash de su sesion activa
        if clave:   #
            self.eliminar_clave(clave, indice)

    def inspeccionar(self):
        #Muestra datos públicos de las sesiones, sin revelar las llaves
        for indice in self.cache.scan_iter(match=config.prefijo + 'cliente:*'): #SCAN recorre claves por lotes y match filtra por el prefijo y cliente
            clave = self.cache.get(indice) #obtiene el HASH al que apunta cada indice
            if clave:
                registro = self.cache.hgetall(clave) #lee el contenido del hash referenciado
                if registro:
                    yield { #entrega una fila a la vez
                        'id_cliente': int(registro['id_cliente']),
                        'tipo': registro['tipo'],
                        'TTL_segundos': self.cache.ttl(clave),
                        'llave_guardada_cifrada': bool(registro.get('llave_sesion')), #muestra solo si existe la llave
                    }
