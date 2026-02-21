window.app = Vue.createApp({
  el: '#vue',
  mixins: [window.windowMixin],
  data() {
    return {
      count: null,
      loading: false,
      incrementAmount: 10,
      incrementInvoice: null,
      incrementWs: null,
      showIncrementDialog: false,
      invoiceForm: {
        wallet_id: null,
        amount: 1,
        memo: 'WasmExample invoice'
      },
      payForm: {
        wallet_id: null,
        payment_request: ''
      },
      lastInvoice: null
    }
  },
  computed: {
    publicUrl() {
      return `${window.location.origin}/wasmexample/public/counter`
    }
  },
  methods: {
    async proxyRequest(method, path, key, body) {
      const {data} = await LNbits.api.request(
        'POST',
        '/wasmexample/api/v1/proxy',
        key,
        {
          method,
          path,
          body
        }
      )
      return data
    },
    async loadCount() {
      this.loading = true
      try {
        const {data} = await LNbits.api.request(
          'GET',
          '/wasmexample/api/v1/kv/counter',
          this.g.user.wallets[0].inkey
        )
        this.count = data.value !== null ? Number(data.value) : 0
      } catch (err) {
        LNbits.utils.notifyApiError(err)
      } finally {
        this.loading = false
      }
    },
    async increment() {
      this.loading = true
      try {
        const {data} = await LNbits.api.request(
          'POST',
          '/wasmexample/api/v1/kv/counter/increment',
          this.g.user.wallets[0].inkey
        )
        this.count = data.value
      } catch (err) {
        LNbits.utils.notifyApiError(err)
      } finally {
        this.loading = false
      }
    },
    async createIncrementInvoice() {
      this.loading = true
      try {
        await LNbits.api.request(
          'POST',
          '/wasmexample/api/v1/kv/increment_amount',
          this.g.user.wallets[0].inkey,
          {value: String(this.incrementAmount)}
        )
        const data = await this.proxyRequest(
          'POST',
          '/api/v1/payments',
          this.g.user.wallets[0].inkey,
          {
            out: false,
            amount: this.incrementAmount,
            unit: 'sat',
            memo: 'WasmExample increment',
            extra: {tag: 'wasmexample:increment'}
          }
        )
        this.incrementInvoice = data
        await LNbits.api.request(
          'POST',
          '/wasmexample/api/v1/watch',
          this.g.user.wallets[0].inkey,
          {
            payment_hash: data.payment_hash,
            handler: 'increment_counter',
            tag: 'wasmexample:increment',
            store_key: 'last_payment'
          }
        )
        this.showIncrementDialog = true
        this.listenForIncrementPayment(data.payment_hash)
      } catch (err) {
        LNbits.utils.notifyApiError(err)
      } finally {
        this.loading = false
      }
    },
    listenForIncrementPayment(paymentHash) {
      if (this.incrementWs) {
        try {
          this.incrementWs.close()
        } catch {}
      }
      const url = new URL(window.location)
      url.protocol = url.protocol === 'https:' ? 'wss' : 'ws'
      url.pathname = `/api/v1/ws/${paymentHash}`
      const ws = new WebSocket(url)
      this.incrementWs = ws
      ws.addEventListener('message', async ({data}) => {
        const payment = JSON.parse(data)
        if (payment.pending === false) {
          ws.close()
          this.incrementWs = null
          await this.loadCount()
          this.showIncrementDialog = false
        }
      })
      ws.addEventListener('error', () => {
        try {
          ws.close()
        } catch {}
      })
    },
    async createInvoice() {
      try {
        const data = await this.proxyRequest(
          'POST',
          '/api/v1/payments',
          this.g.user.wallets[0].inkey,
          {
            out: false,
            amount: this.invoiceForm.amount,
            unit: 'sat',
            memo: this.invoiceForm.memo
          }
        )
        this.lastInvoice = data
      } catch (err) {
        LNbits.utils.notifyApiError(err)
      }
    },
    async payInvoice() {
      try {
        await this.proxyRequest(
          'POST',
          '/api/v1/payments',
          this.g.user.wallets[0].adminkey,
          {
            out: true,
            bolt11: this.payForm.payment_request
          }
        )
        this.payForm.payment_request = ''
        Quasar.Notify.create({
          type: 'positive',
          message: 'Invoice paid'
        })
      } catch (err) {
        LNbits.utils.notifyApiError(err)
      }
    }
  },
  created() {
    this.loadCount()
  }
})
