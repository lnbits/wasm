window.app = Vue.createApp({
  el: '#vue',
  mixins: [window.windowMixin],
  data() {
    return {
      count: null,
      loading: false,
      incrementAmount: 1,
      incrementInvoice: null,
      incrementWs: null,
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
        const {data} = await LNbits.api.request(
          'POST',
          '/wasmexample/api/v1/invoices',
          this.g.user.wallets[0].inkey,
          {
            wallet_id: this.g.user.wallets[0].id,
            amount: this.incrementAmount,
            memo: 'WasmExample increment'
          }
        )
        this.incrementInvoice = data
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
          await this.increment()
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
        const {data} = await LNbits.api.request(
          'POST',
          '/wasmexample/api/v1/invoices',
          this.g.user.wallets[0].inkey,
          this.invoiceForm
        )
        this.lastInvoice = data
      } catch (err) {
        LNbits.utils.notifyApiError(err)
      }
    },
    async payInvoice() {
      try {
        await LNbits.api.request(
          'POST',
          '/wasmexample/api/v1/invoices/pay',
          this.g.user.wallets[0].inkey,
          this.payForm
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
